# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import json
import logging
import re
import uuid
from threading import Event

# Third-party imports
from pyre import Pyre

# Local imports
from ..tools import zmq, green  # , spy_call, w_spy_call, spy_object


logger = logging.getLogger(__name__)


class PyreNode(Pyre):

    def __init__(self, *args, **kwargs):
        # spy_object(self, class_=Pyre, except_=['name', 'uuid'], with_caller=False)
        # spy_call(self.__init__, args, kwargs, with_caller=False); print
        self._name = None
        self._uuid = None
        super(self.__class__, self).__init__(*args, **kwargs)

        self.request_results = {}  # TODO: Fuse the two dicts
        self.request_events = {}

        self.poller = zmq.Poller()
        self.poller.register(self.inbox, zmq.POLLIN)

        self.join('SURVEY')

    def run(self):
        self.task = green.spawn(self._run, 100)

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
                logger.debug('(%s) KeyboardInterrupt or SystemExit', self.name())
                break

        logger.debug('(%s) Exiting loop and stopping', self.name())
        self.stop()

    def _process_message(self):
        logger.debug('(%s) processing message', self.name())

        msg = self.recv()
        logger.debug('(%s) received stuff: %s', self.name(), msg)
        msg_type = msg.pop(0)
        logger.debug('(%s) msg_type: %s', self.name(), msg_type)
        peer_id = uuid.UUID(bytes=msg.pop(0))
        logger.debug('(%s) peer_id: %s', self.name(), peer_id)
        peer_name = msg.pop(0)
        logger.debug('(%s) peer_name: %s', self.name(), peer_name)

        if msg_type == b'ENTER':
            self.on_peer_enter(peer_id, peer_name, msg)

        elif msg_type == b'EXIT':
            self.on_peer_exit(peer_id, peer_name, msg)

        elif msg_type == b'SHOUT':
            self.on_peer_shout(peer_id, peer_name, msg)

        elif msg_type == b'WHISPER':
            self.on_peer_whisper(peer_id, peer_name, msg)

    def on_peer_enter(self, peer_id, peer_name, msg):
        logger.debug('(%s) ZRE ENTER: %s, %s', self.name(), peer_name, peer_id)

        pub_endpoint = self.get_peer_endpoint(peer_id, 'pub')
        rpc_endpoint = self.get_peer_endpoint(peer_id, 'rpc')

        self.on_new_peer(peer_id, peer_name, pub_endpoint, rpc_endpoint)

    def on_new_peer(self, peer_id, peer_name, pub_endpoint, rpc_endpoint):
        pass

    def on_peer_exit(self, peer_id, peer_name, msg):
        logger.debug('(%s) ZRE EXIT: %s, %s', self.name(), peer_name, peer_id)

        self.on_peer_gone(peer_id, peer_name)

    def on_peer_gone(self, peer_id, peer_name):
        pass

    def on_peer_shout(self, peer_id, peer_name, msg):
        group = msg.pop(0)
        data = msg.pop(0)
        logger.debug('(%s) ZRE SHOUT: %s, %s > (%s) %s',
                     self.name(), peer_name, peer_id, group, data)

        if group == b'SURVEY':
            self.on_survey(peer_id, peer_name, json.loads(data))

        elif group == b'EVENT':
            self.on_event(peer_id, peer_name, json.loads(data))

    def on_survey(self, peer_id, peer_name, request):
        pass

    def on_event(self, peer_id, peer_name, request):
        pass

    def on_peer_whisper(self, peer_id, peer_name, msg):
        logger.debug('(%s) ZRE WHISPER: %s, %s > %s', self.name(), peer_name, peer_id, msg)

        reply = json.loads(msg[0])
        if reply['req_id'] in self.request_results:
            logger.debug('(%s) Received reply from %s: %s', self.name(), peer_name, reply['data'])
            self.request_results[reply['req_id']].append((peer_name, reply['data']))

            ev, limit_peers = self.request_events[reply['req_id']]
            if limit_peers and (len(self.request_results[reply['req_id']]) >= limit_peers):
                ev.set()
                green.sleep(0)  # Yield
        else:
            logger.warning(
                '(%s) Discarding reply from %s because the request ID is unknown',
                self.name(), peer_name
            )

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
        # request['req_id'] = ('%x' % randint(0, 0xFFFFFFFF)).encode()
        self.request_results[request['req_id']] = []

        ev = Event()
        self.request_events[request['req_id']] = (ev, limit_peers)

        self.shout('SURVEY', json.dumps(request).encode())

        ev.wait(timeout)

        result = self.request_results[request['req_id']]
        del self.request_results[request['req_id']]
        del self.request_events[request['req_id']]

        return result

    def send_event(self, request):
        self.shout('EVENT', json.dumps(request).encode())

    def reply_survey(self, peer_id, reply):
        self.whisper(peer_id, json.dumps(reply).encode())

    def shutdown(self):
        self._running = False

    def name(self):
        if self._name is None:
            # f = w_spy_call(super(self.__class__, self).name, with_caller=False)
            f = super(self.__class__, self).name
            self._name = f()
        return self._name

    def uuid(self):
        if self._uuid is None:
            # f = w_spy_call(super(self.__class__, self).uuid, with_caller=False)
            f = super(self.__class__, self).uuid
            self._uuid = f()
        return self._uuid
