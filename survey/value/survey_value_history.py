# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyValueHistory(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def process_request(self, peer_id, request_id, uri, time_period):
        logger.debug('(%s) Survey request for history of value %s', self.isac_node.name, uri)

        if uri in self.isac_node.isac_values:
            if '.'.join((uri, 'get_history_impl')) not in self.isac_node.rpc.rpc_service.procedures:
                logger.debug('(%s) I know %s but I don\'t have any history for it. Not responding to survey', self.isac_node.name, uri)
                return

            self.reply(peer_id, request_id, True)
        else:
            logger.debug('(%s) I don\'t know value %s. Not responding to survey', self.isac_node.name, uri)

    def process_result(self, results):
        if results:
            return results[0][0]
        else:
            return None
