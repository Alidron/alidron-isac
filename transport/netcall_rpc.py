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
