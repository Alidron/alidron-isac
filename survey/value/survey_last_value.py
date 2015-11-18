import logging

from .. import Survey

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SurveyLastValue(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 3

    def process_request(self, peer_id, request_id, name):
        logger.debug('Survey request for last value of %s', name)

        if name in self.isac_node.isac_values:
            isac_value = self.isac_node.isac_values[name]
            logger.debug('Responding to survey for %s: (%s) %s', name, isac_value.timestamp, isac_value.value)
            self.reply(peer_id, request_id, (isac_value.value, isac_value.timestamp_float))
        else:
            logger.debug('I don\'t know %s, not responding', name)

    def process_result(self, results):
        max_ts = 0
        max_value = None
        for peer_name, result in results:
            value, ts = result
            if ts > max_ts:
                max_ts = ts
                max_value = value
        return max_value, max_ts
