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

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyLastValue(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 3

    def process_request(self, peer_id, request_id, uri):
        logger.debug('Survey request for last value of %s', uri)

        if uri in self.isac_node.isac_values:
            isac_value = self.isac_node.isac_values[uri]
            logger.debug('Responding to survey for %s: (%s) %s', uri, isac_value.timestamp, isac_value.value)
            # TODO: Actually send back the original source peer_name and peer_uuid. Requires quite some refactoring ...
            self.reply(peer_id, request_id, (isac_value.value, isac_value.timestamp_float, isac_value.tags))
        else:
            logger.debug('I don\'t know %s, not responding', uri)

    def process_result(self, results):
        max_ts = 0.0
        max_data = (None, max_ts, {})
        for peer_name, data in results:
            ts = data[1]
            if ts > max_ts:
                max_ts = ts
                max_data = data
        return tuple(max_data)
