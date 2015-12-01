# Copyright 2015 - Alidron's authors
#
# This file is part of Alidron.
# 
# Alidron is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Alidron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Alidron.  If not, see <http://www.gnu.org/licenses/>.

import logging

from .. import Event

logger = logging.getLogger(__name__)

class ValueMetadataUpdateEvent(Event):

    def send(self, value_name, metadata):
        logger.info('Sending event for a value metadata update for %s', value_name)
        data = {
            'event_name': self.name(),
            'data': (value_name, metadata)
        }
        self.transport.send_event(data)

    def process_event(self, peer_name, data):
        value_name, metadata = data
        logger.info('EVENT value metadata update for %s', value_name)

        if value_name in self.isac_node.isac_values:
            self.isac_node.isac_values[value_name]._set_metadata(metadata)
