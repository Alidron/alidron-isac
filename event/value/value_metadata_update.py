# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from .. import Event

logger = logging.getLogger(__name__)

class ValueMetadataUpdateEvent(Event):

    def send(self, value_uri, metadata, source_peer):
        logger.info('(%s) Sending event for a value metadata update for %s, source peer: %s', self.isac_node.name, value_uri, source_peer)
        data = {
            'event_name': self.name(),
            'data': (value_uri, metadata, source_peer)
        }
        self.transport.send_event(data)

    def process_event(self, peer_name, data):
        value_uri, metadata, source_peer = data
        logger.info('(%s) EVENT value metadata update for %s', self.isac_node.name, value_uri)

        if value_uri in self.isac_node.isac_values:
            self.isac_node.isac_values[value_uri]._set_metadata(metadata, source_peer)
