# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import re
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

        self.rpc_regexp = re.compile('^rpc://(.*?)/(.*)$')
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

        self.transport.run()

        green.sleep(0.1)

    def add_rpc(self, f, name=None):
        if name is None:
            name = f.__name__

        published_uri = 'rpc://%s/%s' % (self.name, name)

        self.rpc.register(f, name=name)

        return published_uri

    def call_rpc(self, uri, *args, **kwargs):
        peer_name, func_name = self.rpc_regexp.match(uri).groups()
        return self.rpc.call_on(peer_name, func_name, *args, **kwargs)

    @property
    def name(self):
        return self.transport.name()

    def name_uuid(self):
        return {'peer_name': self.name, 'peer_uuid': str(self.transport.uuid())}

    def subscribe(self, topic, isac_value):
        self.isac_values[topic] = isac_value
        self.pub_sub.subscribe(topic, isac_value)

    def _sub_callback(self, uri, data):
        logger.debug('(%s) Received update for %s: %s', self.name, uri, data)

        if uri in self.isac_values:
            isac_value = self.isac_values[uri]
            isac_value.update_value_from_isac(*data)

    def survey_value_uri(self, match, timeout=0.5, limit_peers=0):
        return self.surveys_manager.call('SurveyValueUri', match, timeout=timeout, limit_peers=limit_peers)

    def survey_last_value(self, uri, timeout=0.5, limit_peers=3):
        return self.surveys_manager.call('SurveyLastValue', uri, timeout=timeout, limit_peers=limit_peers)

    def survey_value_static_tags(self, uri, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValueStaticTags', uri, timeout=timeout, limit_peers=limit_peers)

    def survey_value_metadata(self, uri, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValueMetadata', uri, timeout=timeout, limit_peers=limit_peers)

    def survey_values_metadata(self, uris, is_re=False, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValuesMetadata', uris, is_re=is_re, timeout=timeout, limit_peers=limit_peers)

    def survey_value_history(self, uri, time_period, timeout=0.5, limit_peers=1):
        return self.surveys_manager.call('SurveyValueHistory', uri, time_period, timeout=timeout, limit_peers=limit_peers)

    def event_isac_value_entering(self, value_uri):
        self.events_manager.send('IsacValueEnteringEvent', value_uri)

    def register_isac_value_entering(self, observer):
        self.events_manager.call('IsacValueEnteringEvent', 'register_observer', observer)

    def unregister_isac_value_entering(self, observer):
        self.events_manager.call('IsacValueEnteringEvent', 'unregister_observer', observer)

    def event_value_metadata_update(self, value_uri, metadata, source_peer):
        self.events_manager.send('ValueMetadataUpdateEvent', value_uri, metadata, source_peer)

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
