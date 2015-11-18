import logging

from .. import Survey

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SurveyValueMetadata(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def process_request(self, peer_id, request_id, name):
        logger.info('Survey request for metadata of %s', name)

        if name in self.isac_node.isac_values:
            isac_value = self.isac_node.isac_values[name]
            print '@@@@@@@', name, id(isac_value), type(isac_value._metadata), isac_value._metadata
            if isac_value.metadata:
                logger.info('Responding to metadata survey for %s', name)
                self.reply(peer_id, request_id, isac_value.metadata)
            else:
                logger.info('I know %s but I don\'t have any metadata for it', name)
        else:
            logger.info('I don\'t know %s, not responding', name)

    def process_result(self, results):
        if results:
            return results[0][1]
        else:
            return None
