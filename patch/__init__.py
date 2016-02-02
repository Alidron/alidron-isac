# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import importlib

pyre_node_patched = importlib.import_module('isac.patch.pyre_patched.pyre_node')
pyre_node_original = importlib.import_module('pyre.pyre_node')
setattr(getattr(pyre_node_original, 'PyreNode'), 'recv_beacon', getattr(pyre_node_patched, 'recv_beacon'))

zbeacon_patched = importlib.import_module('isac.patch.pyre_patched.zbeacon')
zbeacon_original = importlib.import_module('pyre.zbeacon')
setattr(getattr(zbeacon_original, 'ZBeacon'), 'handle_pipe', getattr(zbeacon_patched, 'handle_pipe'))
setattr(getattr(zbeacon_original, 'ZBeacon'), 'send_beacon', getattr(zbeacon_patched, 'send_beacon'))

zhelper_patched = importlib.import_module('isac.patch.pyre_patched.zhelper')
zhelper_original = importlib.import_module('pyre.zhelper')
setattr(zhelper_original, 'get_ifaddrs', getattr(zhelper_patched, 'get_ifaddrs'))
