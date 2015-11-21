import json # TODO: Remove
import logging
from weakref import WeakValueDictionary

from .tools import green_backend, green, zmq

from netcall.green import GreenRPCService as RPCServer
from netcall.green import GreenRPCClient as RPCClient
from netcall.green import RemoteRPCError, JSONSerializer

from .isac_value import IsacValue
from .transport import PyreNode
from .survey import SurveysManager
from .event import EventsManager

logger = logging.getLogger(__name__)

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

        self.transport = PyreNode(name, self.context)
        try:
            self.surveys_manager = SurveysManager(self, self.transport)
            self.events_manager = EventsManager(self, self.transport)
        except:
            self.transport.stop()
            raise

        self.transport.on_new_peer = self._on_new_peer
        self.transport.on_peer_gone = self._on_peer_gone
        self.transport.on_survey = self.surveys_manager.on_survey
        self.transport.on_event = self.events_manager.on_event

        self.transport.set_header('rpc_proto', 'tcp')
        self.transport.set_header('rpc_port', str(self.rpc_service_port))
        self.transport.set_header('pub_proto', 'tcp')
        self.transport.set_header('pub_port', str(self.pub_port))

        self.rpc_service.start()
        self.sub_task = green.spawn(self._read_sub)
        self.transport.run(0.1)

        self.isac_values = WeakValueDictionary() # Should be a weakdict

        green.sleep(0.1)

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
        return self.surveys_manager.call('SurveyValuesMetadata', names, is_re=is_re, timeout=timeout, limit_peers=limit_peers)

    def survey_value_history(self, name, time_period, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValueHistory', name, time_period, timeout=timeout, limit_peers=limit_peers)

    def event_isac_value_entering(self, value_name):
        self.events_manager.send('IsacValueEnteringEvent', value_name)

    def register_isac_value_entering(self, observer):
        self.events_manager.call('IsacValueEnteringEvent', 'register_observer', observer)

    def unregister_isac_value_entering(self, observer):
        self.events_manager.call('IsacValueEnteringEvent', 'unregister_observer', observer)

    def event_value_metadata_update(self, value_name, metadata):
        self.events_manager.send('ValueMetadataUpdateEvent', value_name, metadata)

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

    def serve_forever(self):
        self.transport.task.join()

    def shutdown(self):
        self.running = False

        green.sleep(0.1)

        logger.debug('Shutting down transport')
        self.transport.shutdown()
        logger.debug('Shutting down rpc')
        self.rpc_service.shutdown()
        logger.debug('Shutting down pub')
        self.pub.close(0)
        logger.debug('Shutting down sub')
        self.sub.close(0)

        green.sleep(0.1)
