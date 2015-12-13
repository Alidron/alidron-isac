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

class SurveyValueStaticTags(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def process_request(self, peer_id, request_id, uri):
        logger.info('(%s) Survey request for static tags of %s', self.isac_node.name, uri)

        if uri in self.isac_node.isac_values:
            isac_value = self.isac_node.isac_values[uri]
            if isac_value.static_tags:
                logger.info('(%s) Responding to static tags survey for %s', self.isac_node.name, uri)
                self.reply(peer_id, request_id, isac_value.static_tags)
            else:
                logger.info('(%s) I know %s but I don\'t have any static tags for it', self.isac_node.name, uri)
        else:
            logger.info('(%s) I don\'t know %s, not responding', self.isac_node.name, uri)

    def process_result(self, results):
        if results:
            return results[0][1]
        else:
            return {}
