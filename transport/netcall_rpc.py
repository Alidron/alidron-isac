# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from ..tools import green_backend, green

from netcall.green import GreenRPCService as RPCServer
from netcall.green import GreenRPCClient as RPCClient
from netcall.green import RemoteRPCError, JSONSerializer

logger = logging.getLogger(__name__)

class NetcallRPC(object):

    def __init__(self, context):
        self.context = context

        self.rpc_service = RPCServer(
            green_env=green_backend,
            context=self.context,
            serializer=JSONSerializer()
        )
        self.rpc_service_port = self.rpc_service.bind_ports('*', 0)

        self.rpc_clients = {}

    def setup_transport(self, transport):
        transport.set_header('rpc_proto', 'tcp')
        transport.set_header('rpc_port', str(self.rpc_service_port))

    def start(self):
        self.rpc_service.start()

    def connect(self, peer_id, peer_name, endpoint):
        # connect to rpc server by making an rpc client
        rpc_client = RPCClient(
            green_env=green_backend,
            context=self.context,
            serializer=JSONSerializer()
        )
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
