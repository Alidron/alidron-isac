# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import logging
import re
from functools import reduce

# Third-party imports

# Local imports
from .. import Survey

logger = logging.getLogger(__name__)


class SurveyValueUri(Survey):

    def process_request(self, peer_id, request_id, match):
        logger.debug('(%s) Survey request on value uris matching to %s', self.isac_node.name, match)
        value_uris = self.isac_node.isac_values.keys()

        try:
            match_filter = re.compile(match)
        except re.error as ex:
            logger.warning(
                '(%s) Malformated regular expression from peer %s: "%s" -> %s',
                self.isac_node.name, peer_id, match, str(ex)
            )
            return
        matched_values = list(filter(match_filter.search, value_uris))

        if matched_values:
            logger.debug('(%s) Responding to survey: %s', self.isac_node.name, matched_values)
            self.reply(peer_id, request_id, matched_values)
        else:
            logger.debug('(%s) Nothing to answer to survey', self.isac_node.name)

    def process_result(self, results):
        return set(reduce(lambda res, x: res+x[1], results, []))
