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
        logger.debug('Survey request on value uris matching to %s', match)
        value_uris = self.isac_node.isac_values.keys()

        try:
            match_filter = re.compile(match)
        except re.error, ex:
            logger.warning('Malformated regular expression from peer %s: "%s" -> %s', peer_id, match, ex.message)
            return
        matched_values = filter(match_filter.search, value_uris)

        if matched_values:
            logger.debug('Responding to survey: %s', matched_values)
            self.reply(peer_id, request_id, matched_values)
        else:
            logger.debug('Nothing to answer to survey')

    def process_result(self, results):
        return set(reduce(lambda res,x: res+x[1], results, []))
