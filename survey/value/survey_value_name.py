import logging
import re

from .. import Survey

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SurveyValueName(Survey):

    def process_request(self, peer_id, request_id, match):
        logger.debug('Survey request on value names matching to %s', match)
        value_names = self.isac_node.isac_values.keys()

        try:
            match_filter = re.compile(match)
        except re.error, ex:
            logger.warning('Malformated regular expression from peer %s: "%s" -> %s', peer_id, match, ex.message)
            return
        matched_values = filter(match_filter.search, value_names)

        if matched_values:
            logger.debug('Responding to survey: %s', matched_values)
            self.reply(peer_id, request_id, matched_values)
        else:
            logger.debug('Nothing to answer to survey')

    def process_result(self, results):
        return set(reduce(lambda res,x: res+x[1], results, []))
