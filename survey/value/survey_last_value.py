# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyLastValue(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 3

    def process_request(self, peer_id, request_id, uri):
        logger.debug('(%s) Survey request for last value of %s', self.isac_node.name, uri)

        if uri in self.isac_node.isac_values:
            isac_value = self.isac_node.isac_values[uri]
            logger.debug('(%s) Responding to survey for %s: (%s) %s, %s', self.isac_node.name, uri, isac_value.timestamp, isac_value.value, isac_value.tags)
            self.reply(peer_id, request_id, (isac_value.value, isac_value.timestamp_float, isac_value.tags))
        else:
            logger.debug('(%s) I don\'t know %s, not responding', self.isac_node.name, uri)

    def process_result(self, results):
        max_ts = 0.0
        max_data = (None, max_ts, {})
        for peer_name, data in results:
            ts = data[1]
            if ts > max_ts:
                max_ts = ts
                max_data = data
        return tuple(max_data)
