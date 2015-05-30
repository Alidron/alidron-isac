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

class _PyreNode(Pyre):

    def __init__(self):
        super(_PyreNode, self).__init__()

        self.poller = zmq.Poller()
        self.poller.register(self.inbox, zmq.POLLIN)

    def run(self, timeout=None):
        self.task = green.spawn(self._run, timeout)

    def _run(self, timeout=None):
        self._running = True
        self.start()

        while self._running:
            try:
                #logger.debug('Polling')
                items = dict(self.poller.poll(timeout))
                #logger.debug('polled out: %s, %s', len(items), items)
                while len(items) > 0:
                    for fd, ev in items.items():
                        if (self.inbox == fd) and (ev == zmq.POLLIN):
                            self._process_message()

                    #logger.debug('quick polling')
                    items = dict(self.poller.poll(0))
                    #logger.debug('qpoll: %s, %s', len(items), items)

            except (KeyboardInterrupt, SystemExit):
                logger.debug('KeyboardInterrupt or SystemExit')
                break

        logger.debug('Exiting loop and stopping')
        self.stop()

    def _process_message(self):
        logger.debug('processing message')

        msg = self.recv()
        logger.debug('received stuff: %s', msg)
        msg_type = msg.pop(0)
        logger.debug('msg_type: %s', msg_type)
        peer_id = uuid.UUID(bytes=msg.pop(0))
        logger.debug('peer_id: %s', peer_id)
        peer_name = msg.pop(0)
        logger.debug('peer_name: %s', peer_name)

        if msg_type == 'ENTER':
            self.on_peer_enter(peer_id, peer_name, msg)

        elif msg_type == 'EXIT':
            self.on_peer_exit(peer_id, peer_name, msg)

        elif msg_type == 'SHOUT':
            self.on_peer_shout(peer_id, peer_name, msg)

        elif msg_type == 'WHISPER':
            self.on_peer_whisper(peer_id, peer_name, msg)

    def on_peer_enter(self, peer_id, peer_name, msg):
        logger.info('ZRE ENTER: %s, %s', peer_name, peer_id)

    def on_peer_exit(self, peer_id, peer_name, msg):
        logger.info('ZRE EXIT: %s, %s', peer_name, peer_id)

    def on_peer_shout(self, peer_id, peer_name, msg):
        logger.info('ZRE SHOUT: %s, %s > (%s) %s', peer_name, peer_id, msg[0], msg[1])

    def on_peer_whisper(self, peer_id, peer_name, msg):
        logger.info('ZRE WHISPER: %s, %s > %s', peer_name, peer_id, msg)

    def get_peer_endpoint(self, peer, prefix):
        pyre_endpoint = self.get_peer_address(peer)
        ip = re.search('.*://(.*):.*', pyre_endpoint).group(1)
        return '%s://%s:%s' % (
            self.get_peer_header_value(peer, prefix + '_proto'),
            ip,
            self.get_peer_header_value(peer, prefix + '_port')
        )

    def shutdown(self):
        self._running = False


class IsacNode(object):

    def __init__(self, name, context=zmq.Context()):
        self.context = context

        self.request_results = {} # TODO: Fuse the two dicts
        self.request_events = {}

        self.rpc_service = RPCServer(
            green_env=green_backend,
            serializer=JSONSerializer()
        )
        self.rpc_service_port = self.rpc_service.bind_ports('*', 0)

        self.rpc_clients = {}

        self.pub = self.context.socket(zmq.PUB)
        self.pub_port = self.pub.bind_to_random_port('tcp://*')

        self.sub = self.context.socket(zmq.SUB)

        self.pyre = _PyreNode()
        self.pyre.on_peer_enter = self._on_pyre_peer_enter
        self.pyre.on_peer_exit = self._on_pyre_peer_exit
        self.pyre.on_peer_shout = self._on_pyre_peer_shout
        self.pyre.on_peer_whisper = self._on_pyre_peer_whisper
        self.pyre.set_name(name)
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
        #request = {
        #    'function': 'survey_value_name',
        #    'args': (match,),
        #    'kwargs': {},
        #}
        request = self._make_survey_request('survey_value_name', match)

        results = self._survey(request, timeout, limit_peers)

        return set(reduce(lambda res,x: res+x[1], results, []))

    def survey_last_value(self, name, timeout=0.5, limit_peers=3):
        #request = {
        #    'function': 'survey_last_value',
        #    'args': (name,),
        #    'kwargs': {},
        #}
        request = self._make_survey_request('survey_last_value', name)

        results = self._survey(request, timeout, limit_peers)

        max_ts = 0
        max_value = None
        for peer_name, result in results:
            value, ts = result
            if ts > max_ts:
                max_ts = ts
                max_value = value
        return max_value, max_ts

    def survey_value_metadata(self, name, timeout=0.5, limit_peers=1):
        #request = {
        #    'function': 'survey_value_metadata',
        #    'args': (name,),
        #    'kwargs': {},
        #}
        request = self._make_survey_request('survey_value_metadata', name)

        result = self._survey(request, timeout, limit_peers)

        if result:
            return result[0][1]
        else:
            return None

    def survey_values_metadata(self, names, is_re=False, timeout=0.5, limit_peers=1):
        #request = {
        #    'function': 'survey_values_metadata',
        #    'args': (names,),
        #    'kwargs': {'is_re': is_re},
        #}
        request = self._make_survey_request('survey_values_metadata', names, is_re=is_re)

        results = self._survey(request, timeout, limit_peers)

        all_metadata = {}
        for peer_name, result in results:
            all_metadata.update(result)
        return all_metadata

    def survey_value_history(self, name, time_period, timeout=0.5, limit_peers=1):
        request = self._make_survey_request('survey_value_history', name, time_period)

        result = self._survey(request, timeout, limit_peers)

        if result:
            return result[0][0]
        else:
            return None

    def _make_survey_request(self, function, *args, **kwargs):
        return {
            'req_id': ('%x' % randint(0, 0xFFFFFFFF)).encode(),
            'function': function,
            'args': args,
            'kwargs': kwargs
        }

    def _survey(self, request, timeout=0.5, limit_peers=0):
        #request['req_id'] = ('%x' % randint(0, 0xFFFFFFFF)).encode()
        self.request_results[request['req_id']] = []

        ev = Event()
        self.request_events[request['req_id']] = (ev, limit_peers)

        self.pyre.shout('SURVEY', json.dumps(request))

        ev.wait(timeout)

        result = self.request_results[request['req_id']]
        del self.request_results[request['req_id']]
        del self.request_events[request['req_id']]
        return result

    def _survey_reply(self, peer_id, request_id, data):
        reply = {
            'req_id': request_id,
            'data': data
        }
        self.pyre.whisper(peer_id, json.dumps(reply))

    def do_survey_value_name(self, peer_id, request_id, match):
        logger.debug('Survey request on value names matching to %s', match)
        value_names = self.isac_values.keys()

        match_filter = re.compile(match)
        matched_values = filter(match_filter.search, value_names)

        if matched_values:
            logger.debug('Responding to survey: %s', matched_values)
            self._survey_reply(peer_id, request_id, matched_values)
        else:
            logger.debug('Nothing to answer to survey')

    def do_survey_last_value(self, peer_id, request_id, name):
        logger.debug('Survey request for last value of %s', name)

        if name in self.isac_values:
            isac_value = self.isac_values[name]
            logger.debug('Responding to survey for %s: (%s) %s', name, isac_value.timestamp, isac_value.value)
            self._survey_reply(peer_id, request_id, (isac_value.value, isac_value.timestamp_float))
        else:
            logger.debug('I don\'t know %s, not responding', name)

    def do_survey_value_metadata(self, peer_id, request_id, name):
        logger.info('Survey request for metadata of %s', name)

        if name in self.isac_values:
            isac_value = self.isac_values[name]
            print '@@@@@@@', name, id(isac_value), type(isac_value._metadata), isac_value._metadata
            if isac_value.metadata:
                logger.info('Responding to metadata survey for %s', name)
                self._survey_reply(peer_id, request_id, isac_value.metadata)
            else:
                logger.info('I know %s but I don\'t have any metadata for it', name)
        else:
            logger.info('I don\'t know %s, not responding', name)

    def do_survey_values_metadata(self, peer_id, request_id, names, is_re=False):
        logger.debug('Survey request for metadata for %s', names)

        if is_re:
            match = names
            value_names = self.isac_values.keys()
            match_filter = re.compile(match)
            names = filter(match_filter.search, value_names)

        all_metadata = {}
        if names:
            for name in names:
                if name not in self.isac_values:
                    continue

                isac_value = self.isac_values[name]
                if isac_value.metadata:
                    all_metadata[name] = isac_value.metadata

        if all_metadata:
            logger.debug('Can respond to metadata survey for %d values', len(all_metadata.keys()))
            self._survey_reply(peer_id, request_id, all_metadata)
        else:
            logger.debug('I don\'t have anything to respond to metadata survey')

    def do_survey_value_history(self, peer_id, request_id, name, time_period):
        logger.debug('Survey request for history of value %s', name)

        if name in self.isac_values:
            try:
                self.isac_values[name].get_history_impl
            except AttributeError:
                logger.debug('I know %s but I don\'t have any history for it. Not responding to survey', name)
                return

            self._survey_reply(peer_id, request_id, True)
        else:
            logger.debug('I don\'t know value %s. Not responding to survey', name)

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
        while True:
            logger.debug('Reading on sub')
            data = self.sub.recv_multipart()
            logger.debug('Received update for %s', data[0])
            logger.debug('Value is %s', json.loads(data[1]))
            if data[0] in self.isac_values:
                isac_value = self.isac_values[data[0]]
                isac_value.update_value_from_isac(*json.loads(data[1]))

    def _on_pyre_peer_enter(self, peer_id, peer_name, msg):
        logger.debug('ZRE ENTER: %s, %s', peer_name, peer_id)

        # Connect to pub through sub
        sub_endpoint = self.pyre.get_peer_endpoint(peer_id, 'pub')
        logger.debug('Connecting to PUB endpoint of %s: %s', peer_name, sub_endpoint)
        self.sub.connect(sub_endpoint)

        # connect to rpc server by making an rpc client
        rpc_client = RPCClient(
            green_env=green_backend,
            serializer=JSONSerializer()
        )
        rpc_endpoint = self.pyre.get_peer_endpoint(peer_id, 'rpc')
        logger.debug('Connecting to RPC endpoint of %s: %s', peer_name, sub_endpoint)
        rpc_client.connect(rpc_endpoint)
        self.rpc_clients[peer_name] = (peer_id, rpc_client)

    def _on_pyre_peer_exit(self, peer_id, peer_name, msg):
        logger.debug('ZRE EXIT: %s, %s', peer_name, peer_id)
        # TODO: cleanup sub and rpc connections

    def _on_pyre_peer_shout(self, peer_id, peer_name, msg):
        group = msg.pop(0)
        data = msg.pop(0)
        logger.debug('ZRE SHOUT: %s, %s > (%s) %s', peer_name, peer_id, group, data)

        if group == 'SURVEY':
            self._on_survey(peer_id, data)

        elif group == 'EVENT':
            self._on_event(peer_id, peer_name, data)

    def _on_pyre_peer_whisper(self, peer_id, peer_name, msg):
        logger.debug('ZRE WHISPER: %s, %s > %s', peer_name, peer_id, msg)

        reply = json.loads(msg[0])
        if reply['req_id'] in self.request_results:
            logger.debug('Received reply from %s: %s', peer_name, reply['data'])
            self.request_results[reply['req_id']].append((peer_name, reply['data']))

            ev, limit_peers = self.request_events[reply['req_id']]
            if limit_peers and (len(self.request_results[reply['req_id']]) >= limit_peers):
                ev.set()
                green.sleep(0) # Yield
        else:
            logger.warning('Discarding reply from %s because the request ID is unknown', peer_name)


    def _on_survey(self, peer_id, data):
        request = json.loads(data)

        if request['function'] == 'survey_value_name':
            self.do_survey_value_name(peer_id, request['req_id'], *request['args'], **request['kwargs'])

        elif request['function'] == 'survey_last_value':
            self.do_survey_last_value(peer_id, request['req_id'], *request['args'], **request['kwargs'])

        elif request['function'] == 'survey_value_metadata':
            self.do_survey_value_metadata(peer_id, request['req_id'], *request['args'], **request['kwargs'])

        elif request['function'] == 'survey_values_metadata':
            self.do_survey_values_metadata(peer_id, request['req_id'], *request['args'], **request['kwargs'])

        elif request['function'] == 'survey_value_history':
            self.do_survey_value_history(peer_id, request['req_id'], *request['args'], **request['kwargs'])

    def _on_event(self, peer_id, peer_name, data):
        request = json.loads(data)

        if request['event_name'] == 'isac_value_entering':
            self.do_event_isac_value_entering(peer_name, request['data'])

        if request['event_name'] == 'event_value_metadata_update':
            self.do_event_value_metadata_update(peer_name, request['data'])

    def serve_forever(self):
        self.pyre.task.join()

    def shutdown(self):
        green.sleep(0.1)

        print 'shutting down pyre'
        self.pyre.shutdown()
        print 'shutting down rpc'
        self.rpc_service.shutdown()
        print 'shutting down pub'
        self.pub.close(0)
        print 'shutting down sub'
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

        print '>>>>>', self.name, id(self), type(self._metadata), self._metadata
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
    def value(self):
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
        else:
            logger.warning('Trying to update value %s with a value older than what we have (%f vs. %f)', self.name, ts_float, self.timestamp_float)

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
