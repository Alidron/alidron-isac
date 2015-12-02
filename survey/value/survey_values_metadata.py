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

class SurveyValuesMetadata(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def ask(self, names, is_re=False, **kwargs):
        kwargs['is_re'] = is_re
        return super(self.__class__, self).ask(names, **kwargs)

    def process_request(self, peer_id, request_id, names, is_re=False):
        logger.debug('Survey request for metadata for %s', names)

        if is_re:
            match = names
            value_names = self.isac_node.isac_values.keys()
            try:
                match_filter = re.compile(match)
            except re.error, ex:
                logger.warning('Malformated regular expression from peer %s: "%s" -> %s', peer_id, match, ex.message)
                return
            names = filter(match_filter.search, value_names)
            logger.debug('Found following names: %s', names)

        all_metadata = {}
        if names:
            for name in names:
                if name not in self.isac_node.isac_values:
                    continue

                isac_value = self.isac_node.isac_values[name]
                if isac_value.metadata:
                    all_metadata[name] = isac_value.metadata

        if all_metadata:
            logger.debug('Can respond to metadata survey for %d values', len(all_metadata.keys()))
            self.reply(peer_id, request_id, all_metadata)
        else:
            logger.debug('I don\'t have anything to respond to metadata survey')

    def process_result(self, results):
        logger.debug('Received %s', results)
        all_metadata = {}
        for peer_name, result in results:
            all_metadata.update(result)
        logger.debug('All metadata: %s', all_metadata)
        return all_metadata
