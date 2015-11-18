import json
import logging
import re
import uuid
import time
from datetime import datetime
from random import randint

green_backend = 'gevent'

if green_backend == 'eventlet':
    import eventlet as green
    from eventlet.green import zmq
elif green_backend == 'gevent':
    import gevent as green
    import zmq.green as zmq

from netcall.green import GreenRPCService as RPCServer
from netcall.green import GreenRPCClient as RPCClient
from netcall.green import RemoteRPCError, JSONSerializer
from netcall import concurrency
from pyre import Pyre

from .transport.pyre_node import PyreNode
from .survey import SurveysManager

_tools = concurrency.get_tools(env=green_backend)
Future = _tools.Future
Event = _tools.Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Observable(set):

    def __call__(self, *args, **kwargs):
        for observer in self:
            green.spawn(observer, *args, **kwargs)
            #observer(*args, **kwargs)

    def __iadd__(self, observer):
        self.add(observer)
        return self

    def __isub__(self, observer):
        self.remove(observer)
        return self

    def __repr__(self):
        return "Event(%s)" % set.__repr__(self)


class IsacNode(object):

    def __init__(self, name, context=zmq.Context()):
        self.context = context

        self.running = True

        self.rpc_service = RPCServer(
            green_env=green_backend,
            context=self.context,
            serializer=JSONSerializer()
        )
        self.rpc_service_port = self.rpc_service.bind_ports('*', 0)

        self.rpc_clients = {}

        self.pub = self.context.socket(zmq.PUB)
        self.pub_port = self.pub.bind_to_random_port('tcp://*')

        self.sub = self.context.socket(zmq.SUB)

        self.pyre = PyreNode(name, self.context)
        try:
            self.surveys_manager = SurveysManager(self, self.pyre)
        except:
            self.pyre.stop()
            raise

        self.pyre.on_new_peer = self._on_new_peer
        self.pyre.on_peer_gone = self._on_peer_gone
        self.pyre.on_survey = self.surveys_manager.on_survey
        self.pyre.on_event = self._on_event

        self.pyre.set_header('rpc_proto', 'tcp')
        self.pyre.set_header('rpc_port', str(self.rpc_service_port))
        self.pyre.set_header('pub_proto', 'tcp')
        self.pyre.set_header('pub_port', str(self.pub_port))

        self.rpc_service.start()
        self.sub_task = green.spawn(self._read_sub)
        self.pyre.run(0.1)

        self.isac_values = {} # Should be a weakdict

        green.sleep(0.1)

        self.pyre.join('SURVEY')

        self._isac_value_entering_obs = Observable()

    def subscribe(self, topic, isac_value):
        logger.info('Subscribing to %s', topic)
        self.sub.setsockopt(zmq.SUBSCRIBE, topic)
        self.isac_values[topic] = isac_value

    def survey_value_name(self, match, timeout=0.5, limit_peers=0):
        return self.surveys_manager.call('SurveyValueName', match, timeout=timeout, limit_peers=limit_peers)

    def survey_last_value(self, name, timeout=0.5, limit_peers=3):
        return self.surveys_manager.call('SurveyLastValue', name, timeout=timeout, limit_peers=limit_peers)

    def survey_value_metadata(self, name, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValueMetadata', name, timeout=timeout, limit_peers=limit_peers)

    def survey_values_metadata(self, names, is_re=False, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValuesMetadata', name, is_re=is_re, timeout=timeout, limit_peers=limit_peers)

    def survey_value_history(self, name, time_period, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValueHistory', name, time_period, timeout=timeout, limit_peers=limit_peers)

    def event_isac_value_entering(self, value_name):
        logger.info('Sending event for an entering isac value for %s', value_name)
        data = {
            'event_name': 'isac_value_entering',
            'data': value_name
        }
        self.pyre.shout('EVENT', json.dumps(data))

    def do_event_isac_value_entering(self, peer_name, value_name):
        logger.info('EVENT isac value entering from %s: %s', peer_name, value_name)
        self._isac_value_entering_obs(peer_name, value_name)

    def register_isac_value_entering(self, observer):
        if not self._isac_value_entering_obs:
            self.pyre.join('EVENT')

        logger.debug('Registering %s', observer.__name__)
        self._isac_value_entering_obs += observer

    def unregister_isac_value_entering(self, observer):
        logger.debug('Unregistering %s', observer.__name__)
        self._isac_value_entering_obs -= observer

        if not self._isac_value_entering_obs:
            self.pyre.leave('EVENT')

    def event_value_metadata_update(self, value_name, metadata):
        logger.info('Sending event for a value metadata update for %s', value_name)
        data = {
            'event_name': 'event_value_metadata_update',
            'data': (value_name, metadata)
        }
        self.pyre.shout('EVENT', json.dumps(data))

    def do_event_value_metadata_update(self, peer_name, data):
        value_name, metadata = data
        logger.info('EVENT value metadata update for %s', value_name)

        if value_name in self.isac_values:
            self.isac_values[value_name]._set_metadata(metadata)

    def _read_sub(self):
        while self.running:
            logger.debug('Reading on sub')
            try:
                data = self.sub.recv_multipart()
            except zmq.ZMQError, ex:
                if ex.errno == 88: # "Socket operation on non-socket", basically, socket probably got closed while we were reading
                    continue # Go to the next iteration to either catch self.running == False or give another chance to retry the read

            logger.debug('Received update for %s', data[0])
            logger.debug('Value is %s', json.loads(data[1]))
            if data[0] in self.isac_values:
                isac_value = self.isac_values[data[0]]
                isac_value.update_value_from_isac(*json.loads(data[1]))

    def _on_new_peer(self, peer_id, peer_name, pub_endpoint, rpc_endpoint):
        logger.debug('New peer: %s, %d', peer_name, peer_id)

        # Connect to pub through sub
        logger.debug('Connecting to PUB endpoint of %s: %s', peer_name, pub_endpoint)
        self.sub.connect(pub_endpoint)

        # connect to rpc server by making an rpc client
        rpc_client = RPCClient(
            green_env=green_backend,
            context=self.context,
            serializer=JSONSerializer()
        )
        logger.debug('Connecting to RPC endpoint of %s: %s', peer_name, pub_endpoint)
        rpc_client.connect(rpc_endpoint)
        self.rpc_clients[peer_name] = (peer_id, rpc_client)

    def _on_peer_gone(self, peer_id, peer_name):
        logger.debug('Peer gone: %s, %s', peer_name, peer_id)
        # TODO: cleanup sub and rpc connections

    def _on_event(self, peer_id, peer_name, request):
        if request['event_name'] == 'isac_value_entering':
            self.do_event_isac_value_entering(peer_name, request['data'])

        if request['event_name'] == 'event_value_metadata_update':
            self.do_event_value_metadata_update(peer_name, request['data'])

    def serve_forever(self):
        self.pyre.task.join()

    def shutdown(self):
        self.running = False

        green.sleep(0.1)

        logger.debug('Shutting down pyre')
        self.pyre.shutdown()
        logger.debug('Shutting down rpc')
        self.rpc_service.shutdown()
        logger.debug('Shutting down pub')
        self.pub.close(0)
        logger.debug('Shutting down sub')
        self.sub.close(0)

        green.sleep(0.1)


class IsacValue(object):

    def __init__(self, isac_node, name, initial_value=None, metadata=None, observers=Observable()):
        ts = datetime.now()

        self.isac_node = isac_node
        self.name = name
        self._metadata = metadata
        self.observers = observers
        self.metadata_observers = Observable()

        self.isac_node.rpc_service.register(
            lambda: (self._value, self.timestamp_float),
            name=self.name
        )

        self._value = initial_value
        if initial_value is None:
            self._value, self._timestamp = None, datetime.fromtimestamp(0)
            self.update_value_from_isac(*self.isac_node.survey_last_value(self.name, limit_peers=1))
        elif isinstance(initial_value, tuple):
            last_value, last_ts = self.isac_node.survey_last_value(self.name, limit_peers=1)
            if initial_value[1] > last_ts: # We want to publish our last value to anyone outside
                print 'publishing former value', initial_value
                self.value_ts = initial_value
            else: # We want to notify all our internal subscribers of the newer last value
                self._value, self._timestamp = None, datetime.fromtimestamp(0)
                self.update_value_from_isac(last_value, last_ts)
        else:
            print 'publishing value', initial_value
            self.value_ts = initial_value, ts

        #print '>>>>>', self.name, id(self), type(self._metadata), self._metadata
        if self._metadata:
            self.isac_node.event_value_metadata_update(self.name, self._metadata)

        self.isac_node.subscribe(name, self)

        self.isac_node.event_isac_value_entering(self.name)

    #def register(self, observer):
    #    if observer not in self._observers:
    #        logger.debug('Registering %s on %s', observer.__name__, self.name)
    #        self._observers.append(observer)

    #def unregister(self, observer):
    #    if observer in self._observers:
    #        logger.debug('Unregistering %s from %s', observer.__name__, self.name)
    #        self._observers.remove(observer)

    #def _fire(self, *args, **kwargs):
    #    for observer in self._observers:
    #        green.spawn(observer, *args, **kwargs)

    @property
    def value(self, refresh=True):
        if refresh:
            green.sleep(0.001)
        return self._value

    @value.setter
    def value(self, new_value):
        ts = datetime.now()
        self._value = new_value
        self._timestamp = ts
        self.publish_value(self._value, self._timestamp)

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def timestamp_float(self):
        return time.mktime(self._timestamp.timetuple()) + (self._timestamp.microsecond / 1000000.0)

    @property
    def value_ts(self):
        return self._value, self._timestamp

    @value_ts.setter
    def value_ts(self, args):
        value, ts = args
        self._value = value
        if isinstance(ts, datetime):
            self._timestamp = ts
        else:
            self._timestamp = datetime.fromtimestamp(ts)

        self.publish_value(self._value, self._timestamp)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata
        self.isac_node.event_value_metadata_update(self.name, self._metadata)

    def _set_metadata(self, metadata):
        self._metadata = metadata
        if self._metadata:
            self.metadata_observers(self.name, self._metadata)

    def update_value_from_isac(self, new_value, ts_float):
        if ts_float > self.timestamp_float:
            self._value = new_value
            self._timestamp = datetime.fromtimestamp(ts_float)
            self.observers(self.name, self._value, self._timestamp)
        elif ts_float < self.timestamp_float:
            logger.warning('Trying to update value %s with a value older than what we have (%f vs. %f)', self.name, ts_float, self.timestamp_float)
        # else equal time => do nothing

    def publish_value(self, value, ts):
        ts_float = self.timestamp_float
        logger.info('Publishing for %s: %s, %s', self.name, value, ts_float)
        self.isac_node.pub.send_multipart([
            self.name,
            json.dumps((value, ts_float))
        ])

    def survey_metadata(self):
        self._set_metadata(self.isac_node.survey_value_metadata(self.name))

    def get_history(self, time_period):
        peer_name = self.isac_node.survey_value_history(self.name, time_period)
        if not peer_name:
            raise Exception('Could not find any peer that could provide history for %s' % self.name)

        t1, t2 = time_period
        if isinstance(t1, datetime):
            t1 = time.mktime(t1.timetuple()) + (t1.microsecond * 1e-6)
        if isinstance(t2, datetime):
            t2 = time.mktime(t2.timetuple()) + (t2.microsecond * 1e-6)

        data = self.isac_node.rpc_clients[peer_name][1].call('.'.join((self.name, 'get_history_impl')), args=[(t1, t2)])
        return [(point[0], datetime.fromtimestamp(point[1])) for point in data]

    def __str__(self):
        return '{0}: {1}'.format(self.timestamp, self.value)

if __name__ == '__main__':
    def p():
        green.sleep(0.1)

    def stop():
        n.shutdown()
        p()

    import sys
    n = IsacNode(sys.argv[1])

    @n.rpc_service.register(name='list')
    def list_():
        return n.rpc_service.procedures.keys()

    p()

    if sys.argv[1] == 'test01':
        val1 = IsacValue(n, 'this.is.a.test', 12)
    else:
        val1 = IsacValue(n, 'this.is.a.test')

    if sys.argv[1] == 'test02':
        val2 = IsacValue(n, 'this.is.another.test', 42)
    else:
        val2 = IsacValue(n, 'this.is.another.test')

    def notifyer(name, value, ts):
        print name, value, ts

    val1.observers += notifyer
    val2.observers += notifyer

    green.sleep(15)

    print val1
    print val2

    n.shutdown()
