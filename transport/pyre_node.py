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
import re
import uuid

from pyre import Pyre

from ..tools import Event, zmq, green

logger = logging.getLogger(__name__)

class PyreNode(Pyre):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.request_results = {} # TODO: Fuse the two dicts
        self.request_events = {}

        self.poller = zmq.Poller()
        self.poller.register(self.inbox, zmq.POLLIN)

        self.join('SURVEY')

    def run(self, timeout=None):
        self.task = green.spawn(self._run, timeout)

    def _run(self, timeout=None):
        self._running = True
        self.start()

        while self._running:
            try:
                # logger.debug('Polling')
                items = dict(self.poller.poll(timeout))
                # logger.debug('polled out: %s, %s', len(items), items)
                while len(items) > 0:
                    for fd, ev in items.items():
                        if (self.inbox == fd) and (ev == zmq.POLLIN):
                            self._process_message()

                    # logger.debug('quick polling')
                    items = dict(self.poller.poll(0))
                    # logger.debug('qpoll: %s, %s', len(items), items)

            except (KeyboardInterrupt, SystemExit):
                logger.debug('KeyboardInterrupt or SystemExit')
                break

        logger.debug('Exiting loop and stopping')
        self.stop()

    def _process_message(self):
        logger.debug('processing message')

        msg = self.recv()
        logger.debug('received stuff: %s', msg)
        msg_type = msg.pop(0)
        logger.debug('msg_type: %s', msg_type)
        peer_id = uuid.UUID(bytes=msg.pop(0))
        logger.debug('peer_id: %s', peer_id)
        peer_name = msg.pop(0)
        logger.debug('peer_name: %s', peer_name)

        if msg_type == 'ENTER':
            self.on_peer_enter(peer_id, peer_name, msg)

        elif msg_type == 'EXIT':
            self.on_peer_exit(peer_id, peer_name, msg)

        elif msg_type == 'SHOUT':
            self.on_peer_shout(peer_id, peer_name, msg)

        elif msg_type == 'WHISPER':
            self.on_peer_whisper(peer_id, peer_name, msg)

    def on_peer_enter(self, peer_id, peer_name, msg):
        logger.debug('ZRE ENTER: %s, %s', peer_name, peer_id)

        pub_endpoint = self.get_peer_endpoint(peer_id, 'pub')
        rpc_endpoint = self.get_peer_endpoint(peer_id, 'rpc')

        self.on_new_peer(peer_id, peer_name, pub_endpoint, rpc_endpoint)

    def on_new_peer(self, peer_id, peer_name, pub_endpoint, rpc_endpoint):
        pass

    def on_peer_exit(self, peer_id, peer_name, msg):
        logger.debug('ZRE EXIT: %s, %s', peer_name, peer_id)

        self.on_peer_gone(peer_id, peer_name)

    def on_peer_gone(self, peer_id, peer_name):
        pass

    def on_peer_shout(self, peer_id, peer_name, msg):
        group = msg.pop(0)
        data = msg.pop(0)
        logger.debug('ZRE SHOUT: %s, %s > (%s) %s', peer_name, peer_id, group, data)

        if group == 'SURVEY':
            self.on_survey(peer_id, peer_name, json.loads(data))

        elif group == 'EVENT':
            self.on_event(peer_id, peer_name, json.loads(data))

    def on_survey(self, peer_id, peer_name, request):
        pass

    def on_event(self, peer_id, peer_name, request):
        pass

    def on_peer_whisper(self, peer_id, peer_name, msg):
        logger.debug('ZRE WHISPER: %s, %s > %s', peer_name, peer_id, msg)

        reply = json.loads(msg[0])
        if reply['req_id'] in self.request_results:
            logger.debug('Received reply from %s: %s', peer_name, reply['data'])
            self.request_results[reply['req_id']].append((peer_name, reply['data']))

            ev, limit_peers = self.request_events[reply['req_id']]
            if limit_peers and (len(self.request_results[reply['req_id']]) >= limit_peers):
                ev.set()
                green.sleep(0) # Yield
        else:
            logger.warning('Discarding reply from %s because the request ID is unknown', peer_name)

    def get_peer_endpoint(self, peer, prefix):
        pyre_endpoint = self.peer_address(peer)
        ip = re.search('.*://(.*):.*', pyre_endpoint).group(1)
        return '%s://%s:%s' % (
            self.peer_header_value(peer, prefix + '_proto'),
            ip,
            self.peer_header_value(peer, prefix + '_port')
        )

    def join_event(self):
        self.join('EVENT')

    def leave_event(self):
        self.leave('EVENT')

    def send_survey(self, request, timeout, limit_peers):
        #request['req_id'] = ('%x' % randint(0, 0xFFFFFFFF)).encode()
        self.request_results[request['req_id']] = []

        ev = Event()
        self.request_events[request['req_id']] = (ev, limit_peers)

        self.shout('SURVEY', json.dumps(request))

        ev.wait(timeout)

        result = self.request_results[request['req_id']]
        del self.request_results[request['req_id']]
        del self.request_events[request['req_id']]

        return result

    def send_event(self, request):
        self.shout('EVENT', json.dumps(request))

    def reply_survey(self, peer_id, reply):
        self.whisper(peer_id, json.dumps(reply))

    def shutdown(self):
        self._running = False
