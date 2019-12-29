# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gevent import monkey
monkey.patch_all()

# System imports
import importlib  # noqa: F402

# Third-party imports

# Local imports

# Patch pyzmq
zmq_patched = importlib.import_module('zmq.green')
del zmq_patched.core._Socket.set  # Suppress useless, bothering warning
zmq_original = importlib.import_module('zmq')
# Make green implementation used by any third-party module (ie. pyre) importing zmq directly
zmq_original.Context = zmq_patched.Context
zmq_original.Socket = zmq_patched.Socket
zmq_original.Poller = zmq_patched.Poller

# Patch pyre (pyre_node) for alidron-repeater use case
pyre_node_patched = importlib.import_module('isac.patch.pyre_patched.pyre_node')
pyre_node_original = importlib.import_module('pyre.pyre_node')
setattr(getattr(pyre_node_original, 'PyreNode'), 'recv_beacon',
        getattr(pyre_node_patched, 'recv_beacon'))

# Patch pyre (zbeacon) for alidron-repeater use case
zbeacon_patched = importlib.import_module('isac.patch.pyre_patched.zbeacon')
zbeacon_original = importlib.import_module('pyre.zbeacon')
setattr(getattr(zbeacon_original, 'ZBeacon'), 'handle_pipe',
        getattr(zbeacon_patched, 'handle_pipe'))
setattr(getattr(zbeacon_original, 'ZBeacon'), 'send_beacon',
        getattr(zbeacon_patched, 'send_beacon'))

# Patch pyre (zhelper) for old alpine/musel bug (TODO: review)
zhelper_patched = importlib.import_module('isac.patch.pyre_patched.zhelper')
zhelper_original = importlib.import_module('pyre.zhelper')
setattr(zhelper_original, 'get_ifaddrs', getattr(zhelper_patched, 'get_ifaddrs'))
