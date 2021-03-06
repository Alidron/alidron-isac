# Copyright - Pyre's authors
# Copyright 2015-2020 - Alidron's authors
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

# System imports
import socket
import struct
import time

# Third-party imports
from pyre.zbeacon import logger, INTERVAL_DFLT, ENETDOWN, ENETUNREACH

# Local imports


def handle_pipe(self):
    #  Get just the commands off the pipe
    request = self.pipe.recv_multipart()
    command = request.pop(0).decode('UTF-8')
    if not command:
        return -1  # Interrupted

    if self.verbose:
        logger.debug("zbeacon: API command={0}".format(command))

    if command == "VERBOSE":
        self.verbose = True
    elif command == "CONFIGURE":
        port = struct.unpack('I', request.pop(0))[0]
        self.configure(port)
    elif command == "PUBLISH":
        self.transmit = request.pop(0)
        if self.interval == 0:
            self.interval = INTERVAL_DFLT
        # Start broadcasting immediately
        self.ping_at = time.time()
    elif command == "SILENCE":
        self.transmit = None
    elif command == "SUBSCRIBE":
        self.filter = request.pop(0)
    elif command == "UNSUBSCRIBE":
        self.filter = None
    elif command == "SEND BEACON":
        self.send_beacon(request.pop(0))
    elif command == "$TERM":
        self.terminated = True
    else:
        logger.error("zbeacon: - invalid command: {0}".format(command))


handle_pipe._patched = True


def send_beacon(self, data=None):
    if data is None:
        data = self.transmit
    try:
        self.udpsock.sendto(data, (str(self.broadcast_address), self.port_nbr))
    except OSError as e:
        # network down, just wait, it could come back up again.
        # socket call errors 50 and 51 relate to the network being
        # down or unreachable, the recommended action to take is to
        # try again so we don't terminate in these cases.
        if e.errno in [ENETDOWN, ENETUNREACH]:
            pass

        # all other cases, we'll terminate
        else:
            logger.debug("Network seems gone, exiting zbeacon")
            self.terminated = True

    except socket.error:
        logger.debug("Network seems gone, exiting zbeacon")
        self.terminated = True


send_beacon._patched = True
