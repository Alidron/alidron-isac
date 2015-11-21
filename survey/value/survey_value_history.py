import logging

from .. import Survey

logger = logging.getLogger(__name__)

class SurveyValueHistory(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def process_request(self, peer_id, request_id, name, time_period):
        logger.debug('Survey request for history of value %s', name)

        if name in self.isac_node.isac_values:
            try:
                self.isac_node.isac_values[name].get_history_impl
                # TODO: Interface to check if the IV can answer for this time period
            except AttributeError:
                logger.debug('I know %s but I don\'t have any history for it. Not responding to survey', name)
                return

            self.reply(peer_id, request_id, True)
        else:
            logger.debug('I don\'t know value %s. Not responding to survey', name)

    def process_result(self, results):
        if results:
            return results[0][0]
        else:
            return None
