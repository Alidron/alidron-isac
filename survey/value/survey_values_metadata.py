import logging
import re

from .. import Survey

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SurveyValuesMetadata(Survey):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.limit_peers = 1

    def ask(self, names, is_re=False, **kwargs):
        kwargs['is_re'] = is_re
        super(self.__class__, self).ask(names, **kwargs)

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
        all_metadata = {}
        for peer_name, result in results:
            all_metadata.update(result)
        return all_metadata
