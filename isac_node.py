import logging
from weakref import WeakValueDictionary

from .tools import green, zmq

from .isac_value import IsacValue
from .transport import PyreNode, NetcallRPC, ZmqPubSub
from .survey import SurveysManager
from .event import EventsManager

logger = logging.getLogger(__name__)

class IsacNode(object):

    def __init__(self, name, context=zmq.Context()):
        self.isac_values = WeakValueDictionary() # Should be a weakdict

        self.rpc = NetcallRPC(context)
        self.pub_sub = ZmqPubSub(context, self._sub_callback)

        self.transport = PyreNode(name, context)
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

        self.rpc.setup_transport(self.transport)
        self.pub_sub.setup_transport(self.transport)
        self.rpc.start()
        self.pub_sub.start()

        self.transport.run(0.1)

        green.sleep(0.1)

    def subscribe(self, topic, isac_value):
        self.isac_values[topic] = isac_value
        self.pub_sub.subscribe(topic, isac_value)

    def _sub_callback(self, name, data):
        logger.debug('Received update for %s', name)
        logger.debug('Value is %s', data)

        if name in self.isac_values:
            isac_value = self.isac_values[name]
            isac_value.update_value_from_isac(*data)

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

    def _on_new_peer(self, peer_id, peer_name, pub_endpoint, rpc_endpoint):
        logger.debug('New peer: %s, %d', peer_name, peer_id)

        self.pub_sub.connect(peer_id, peer_name, pub_endpoint)
        self.rpc.connect(peer_id, peer_name, rpc_endpoint)

    def _on_peer_gone(self, peer_id, peer_name):
        logger.debug('Peer gone: %s, %s', peer_name, peer_id)
        # TODO: cleanup sub and rpc connections

    def serve_forever(self):
        self.transport.task.join()

    def shutdown(self):
        logger.debug('Shutting down transport')
        self.transport.shutdown()

        self.rpc.shutdown()
        self.pub_sub.shutdown()

        green.sleep(0.1)
