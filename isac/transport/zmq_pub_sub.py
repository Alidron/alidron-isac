# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import json
import logging

# Third-party imports

# Local imports
from ..tools import green, zmq


logger = logging.getLogger(__name__)


class ZmqPubSub(object):

    def __init__(self, context, callback):
        self.context = context
        self.callback = callback

        self.pub = self.context.socket(zmq.PUB)
        self.pub_port = self.pub.bind_to_random_port('tcp://*')

        self.sub = self.context.socket(zmq.SUB)

    def setup_transport(self, transport):
        transport.set_header('pub_proto', 'tcp')
        transport.set_header('pub_port', str(self.pub_port))

    def start(self):
        self.running = True
        self.sub_task = green.spawn(self._read_sub)

    def subscribe(self, topic, isac_value):
        logger.info('Subscribing to %s', topic)
        self.sub.setsockopt(zmq.SUBSCRIBE, topic.encode())

    def connect(self, peer_id, peer_name, endpoint):
        # Connect to pub through sub
        logger.debug('Connecting to PUB endpoint of %s: %s', peer_name, endpoint)
        self.sub.connect(endpoint)

    def publish(self, topic, data):
        logger.debug('Sending on PUB: %r, %r', topic, data)
        self.pub.send_multipart([
            topic.encode(),
            json.dumps(data).encode()
        ])

    def _read_sub(self):
        while self.running:
            logger.debug('Reading on sub')
            try:
                data = self.sub.recv_multipart()
                logger.debug('Read on SUB: %r', data)
            except zmq.ZMQError as ex:
                if ex.errno == 88:  # "Socket operation on non-socket", basically, socket probably got closed while we were reading
                    continue  # Go to the next iteration to either catch self.running == False or give another chance to retry the read

            self.callback(data[0].decode(), json.loads(data[1]))

    def shutdown(self):
        self.running = False
        green.sleep(0.1)

        logger.debug('Shutting down PUB')
        self.pub.close(0)
        logger.debug('Shutting down SUB')
        self.sub.close(0)
