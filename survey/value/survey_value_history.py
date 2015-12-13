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
