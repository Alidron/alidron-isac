import logging

from .. import Event

logger = logging.getLogger(__name__)

class ValueMetadataUpdateEvent(Event):

    def send(self, value_name, metadata):
        logger.info('Sending event for a value metadata update for %s', value_name)
        data = {
            'event_name': self.name(),
            'data': (value_name, metadata)
        }
        self.transport.send_event(data)

    def process_event(self, peer_name, data):
        value_name, metadata = data
        logger.info('EVENT value metadata update for %s', value_name)

        if value_name in self.isac_node.isac_values:
            self.isac_node.isac_values[value_name]._set_metadata(metadata)
