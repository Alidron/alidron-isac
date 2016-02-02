# Copyright - Pyre's authors
# Copyright 2015-2016 - Alidron's authors
#
# This file is part of Alidron, based on an extract from Pyre.
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

import ipaddress
import socket
import struct
import uuid

from pyre.pyre_node import BEACON_VERSION, logger


def recv_beacon(self):
    # Get IP address and beacon of peer
    try:
        ipaddress, frame = self.beacon_socket.recv_multipart()
    except ValueError:
        return

    beacon = struct.unpack('cccb16sH', frame[:22])
    # Ignore anything that isn't a valid beacon
    if beacon[3] != BEACON_VERSION:
        logger.warning("Invalid ZRE Beacon version: {0}".format(beacon[3]))
        return

    if len(frame) > 22:
        ipaddress = frame[22:]

    peer_id = uuid.UUID(bytes=beacon[4])
    #print("peerId: %s", peer_id)
    port = socket.ntohs(beacon[5])
    # if we receive a beacon with port 0 this means the peer exited
    if port:
        endpoint = "tcp://%s:%d" %(ipaddress.decode('UTF-8'), port)
        peer = self.require_peer(peer_id, endpoint)
        peer.refresh()
    else:
        # Zero port means peer is going away; remove it if
        # we had any knowledge of it already
        peer = self.peers.get(peer_id)
        # remove the peer (delete)
        if peer:
            logger.debug("Received 0 port beacon, removing peer {0}".format(peer))
            self.remove_peer(peer)

        else:
            logger.warning(self.peers)
            logger.warning("We don't know peer id {0}".format(peer_id))

recv_beacon._patched = True
