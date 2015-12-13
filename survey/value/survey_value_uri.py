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
import re

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyValueUri(Survey):

    def process_request(self, peer_id, request_id, match):
        logger.debug('(%s) Survey request on value uris matching to %s', self.isac_node.name, match)
        value_uris = self.isac_node.isac_values.keys()

        try:
            match_filter = re.compile(match)
        except re.error, ex:
            logger.warning('(%s) Malformated regular expression from peer %s: "%s" -> %s', self.isac_node.name, peer_id, match, ex.message)
            return
        matched_values = filter(match_filter.search, value_uris)

        if matched_values:
            logger.debug('(%s) Responding to survey: %s', self.isac_node.name, matched_values)
            self.reply(peer_id, request_id, matched_values)
        else:
            logger.debug('(%s) Nothing to answer to survey', self.isac_node.name)

    def process_result(self, results):
        return set(reduce(lambda res,x: res+x[1], results, []))
