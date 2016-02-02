# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyValueMetadata(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def process_request(self, peer_id, request_id, uri):
        logger.info('(%s) Survey request for metadata of %s', self.isac_node.name, uri)

        if uri in self.isac_node.isac_values:
            isac_value = self.isac_node.isac_values[uri]
            #print '@@@@@@@', uri, id(isac_value), type(isac_value._metadata), isac_value._metadata
            if isac_value.metadata:
                logger.info('(%s) Responding to metadata survey for %s: %s', self.isac_node.name, uri, self.isac_node.name_uuid())
                self.reply(peer_id, request_id, (isac_value.metadata, self.isac_node.name_uuid()))
            else:
                logger.info('(%s) I know %s but I don\'t have any metadata for it', self.isac_node.name, uri)
        else:
            logger.info('(%s) I don\'t know %s, not responding', self.isac_node.name, uri)

    def process_result(self, results):
        if results:
            return tuple(results[0][1])
        else:
            return (None, None)
