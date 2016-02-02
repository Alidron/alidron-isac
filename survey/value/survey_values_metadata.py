# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import re

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyValuesMetadata(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def ask(self, uris, is_re=False, **kwargs):
        kwargs['is_re'] = is_re
        return super(self.__class__, self).ask(uris, **kwargs)

    def process_request(self, peer_id, request_id, uris, is_re=False):
        logger.debug('(%s) Survey request for metadata for %s', self.isac_node.name, uris)

        if is_re:
            match = uris
            value_uris = self.isac_node.isac_values.keys()
            try:
                match_filter = re.compile(match)
            except re.error, ex:
                logger.warning('(%s) Malformated regular expression from peer %s: "%s" -> %s', self.isac_node.name, peer_id, match, ex.message)
                return
            uris = filter(match_filter.search, value_uris)
            logger.debug('(%s) Found following uris: %s', self.isac_node.name, uris)

        all_metadata = {}
        if uris:
            for uri in uris:
                if uri not in self.isac_node.isac_values:
                    continue

                isac_value = self.isac_node.isac_values[uri]
                if isac_value.metadata:
                    all_metadata[uri] = isac_value.metadata

        if all_metadata:
            logger.debug('(%s) Can respond to metadata survey for %d values', self.isac_node.name, len(all_metadata.keys()))
            self.reply(peer_id, request_id, all_metadata)
        else:
            logger.debug('(%s) I don\'t have anything to respond to metadata survey', self.isac_node.name)

    def process_result(self, results):
        logger.debug('(%s) Received %s', self.isac_node.name, results)
        all_metadata = {}
        for peer_name, result in results:
            all_metadata.update(result)
        logger.debug('(%s) All metadata: %s', self.isac_node.name, all_metadata)
        return all_metadata
