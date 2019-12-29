# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import json
import logging
from itertools import chain
from random import randint
from sys import exc_info
from traceback import format_exc

# Third-party imports

# Local imports
from ..tools import green, zmq, Executor


logger = logging.getLogger(__name__)


class ZmqRPC(object):

    def __init__(self):
        self.rpc_service = _ZmqRouterSocket()
        self.rpc_service_port = self.rpc_service.bind('*', 0)

        self.rpc_clients = {}

    def setup_transport(self, transport):
        transport.set_header('rpc_proto', 'tcp')
        transport.set_header('rpc_port', str(self.rpc_service_port))

    def start(self):
        self.rpc_service.start()
        pass

    def connect(self, peer_id, peer_name, endpoint):
        # connect to rpc server by making an rpc client
        rpc_client = _ZmqDealerSocket()
        logger.debug('Connecting to RPC endpoint of %s: %s', peer_name, endpoint)
        rpc_client.connect(endpoint)
        self.rpc_clients[peer_name] = (peer_id, rpc_client)

    def register(self, func, name=None):
        self.rpc_service.register(func, name=name)

    def unregister(self, name):
        if name in self.rpc_service.procedures:
            del self.rpc_service.procedures[name]

    def call_on(self, peer_name, func_name, *args, **kwargs):
        return self.rpc_clients[peer_name][1].call(func_name, args=args, kwargs=kwargs)

    def shutdown(self):
        logger.debug('Shutting down RPC')
        self.rpc_service.shutdown()


class RPCError(Exception):
    pass


class RemoteRPCError(RPCError):

    def __init__(self, ename, evalue, tb):
        self.ename = ename
        self.evalue = evalue
        self.traceback = tb
        self.args = (ename, evalue)

    def __repr__(self):
        return f'<RemoteError:{self.ename}({self.evalue})'

    def __str__(self):
        if self.traceback:
            return self.traceback
        else:
            return f'{self.ename}({self.evalue})'


class _ZmqBaseSocket(object):

    def __init__(self, identity=None):
        self.context = zmq.Context.instance()

        if not identity:
            identity = ('%08x' % randint(0, 0xFFFFFFFF)).encode()
        self.identity = identity
        self.socket = None
        self.reset()

    def _create_socket(self):
        pass

    def reset(self):
        if self.socket:
            self.socket.close(linger=0)
        self._create_socket()

    def shutdown(self):
        self.socket.close(0)

    def bind(self, ip, ports):
        if isinstance(ports, int):
            ports = [ports]

        for port in ports:
            try:
                if port == 0:
                    port = self.socket.bind_to_random_port(f'tcp://{ip}')
                else:
                    self.socket.bind(f'tcp://{ip}:{port}')
            except (zmq.ZMQError, zmq.ZMQBindError):
                continue
            else:
                break
        else:
            raise zmq.ZMQBindError('No available port')

        return port

    def connect(self, url):
        self.socket.connect(url)


class _ZmqDealerSocket(_ZmqBaseSocket):

    def _create_socket(self):
        super()._create_socket()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity)

    def call(self, proc_name, args=[], kwargs={}):
        # Build request
        req_id = ('%x' % randint(0, 0xFFFFFFFF)).encode()
        msg_list = [b'|', req_id, proc_name.encode()]
        args_ser = json.dumps(args).encode()
        kwargs_ser = json.dumps(kwargs).encode()
        msg_list.append(args_ser)
        msg_list.append(kwargs_ser)

        # Send
        logger.debug('Sending %r', msg_list)
        self.socket.send_multipart(msg_list)

        # Receive response and validate
        msg_list = self.socket.recv_multipart()
        if (len(msg_list) < 4) or (msg_list[0] != b'|'):
            logger.error('Bad reply %r', msg_list)
            return None

        # Parse response
        recv_req_id = msg_list[1]
        msg_type = msg_list[2]
        if msg_type == b'OK':
            return json.loads(msg_list[3])

        elif msg_type == b'FAIL':
            error = json.loads(msg_list[3])
            raise RemoteRPCError(error['ename'], error['evalue'], error['traceback'])

        else:
            raise RPCError(f'Bad message type: {msg_type}')


class _ZmqRouterSocket(_ZmqBaseSocket):

    _RESERVED = [
        '__init__', '_create_socket', 'reset', 'shutdown', 'bind', 'connect',
        'register', '_loop', '_handle_request', '_send_ok', '_send_fail', 'start', 'stop', 'serve',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self.procedures = {}
        self._task = None
        self._executor = Executor(limit=1024)

    def _create_socket(self):
        super()._create_socket()
        self.socket = self.context.socket(zmq.ROUTER)

    def register(self, func=None, name=None):
        if func is None:
            if name is None:
                raise ValueError('Provide at least one of func/name')

            return partial(self.register, name=name)

        else:
            if not callable(func):
                raise ValueError('Func should be callable')
            if name is None:
                name = func.__name__
            if name in self._RESERVED:
                raise ValueError(f'{name} is reserved')

            self.procedures[name] = func

        return func

    def _loop(self):
        logger.debug('ZMQ Router reading loop started')
        while True:
            try:
                request = self.socket.recv_multipart()
            except Exception as ex:
                logger.warning(ex)
                break
            logger.debug('Received: %r', request)
            self._executor.submit(self._handle_request, request)

        logger.debug('ZMQ Router reading loop stopped')

    def _handle_request(self, msg_list):
        # Parse request
        if (len(msg_list) < 6) or (b'|' not in msg_list):
            logger.error('Bad request %r', msg_list)
            return

        boundary = msg_list.index(b'|')
        route = msg_list[0:boundary]
        req_id = msg_list[boundary + 1]
        name = msg_list[boundary + 2].decode()
        proc = self.procedures.get(name, None)

        args = json.loads(msg_list[boundary+3])
        kwargs = json.loads(msg_list[boundary+4])

        if proc is None:
            raise NotImplementedError(f'Unknown procedure {name}')

        # Actual call
        try:
            result = proc(*args, **kwargs)
        except Exception as ex:
            logger.exception('Exception while executing RPC request')
            self._send_fail(route, req_id)
        else:
            self._send_ok(route, req_id, result)

    def _send_ok(self, route, req_id, result):
        data = json.dumps(result).encode()
        reply = list(chain(route, [b'|', req_id, b'OK', data]))
        logger.debug('Sending: %r', reply)
        self.socket.send_multipart(reply)

    def _send_fail(self, route, req_id):
        etype, evalue, tb = exc_info()
        error_dict = dict(
            ename=etype.__name__,
            evalue=str(evalue),
            traceback=format_exc()
        )
        data = json.dumps(error_dict).encode()
        reply = list(chain(route, [b'|', req_id, b'FAIL', data]))
        logger.debug('Sending: %r', reply)
        self.socket.send_multipart(reply)

    def start(self):
        self._task = self._executor.submit(self._loop)
        return self._task

    def stop(self):
        if not self._task:
            return

        self.reset()
        self._task.exception(timeout=0.3)
        self._task.cancel()
        self._task = None

    def shutdown(self):
        self.stop()
        self.socket.close(0)
        self._executor.shutdown(cancel=True)

    def serve(self):
        if not self._task:
            self.start()

        return self._task.result()
