# Copyright 2015 - Alidron's authors
#
# This file is part of Alidron.
# 
# Alidron is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Alidron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with Alidron.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging

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
        self.sub.setsockopt(zmq.SUBSCRIBE, topic)

    def connect(self, peer_id, peer_name, endpoint):
        # Connect to pub through sub
        logger.debug('Connecting to PUB endpoint of %s: %s', peer_name, endpoint)
        self.sub.connect(endpoint)

    def publish(self, topic, data):
        self.pub.send_multipart([
            topic,
            json.dumps(data)
        ])

    def _read_sub(self):
        while self.running:
            logger.debug('Reading on sub')
            try:
                data = self.sub.recv_multipart()
            except zmq.ZMQError, ex:
                if ex.errno == 88: # "Socket operation on non-socket", basically, socket probably got closed while we were reading
                    continue # Go to the next iteration to either catch self.running == False or give another chance to retry the read

            self.callback(data[0], json.loads(data[1]))

    def shutdown(self):
        self.running = False
        green.sleep(0.1)

        logger.debug('Shutting down PUB')
        self.pub.close(0)
        logger.debug('Shutting down SUB')
        self.sub.close(0)
