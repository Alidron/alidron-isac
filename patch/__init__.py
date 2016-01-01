# Copyright 2016 - Alidron's authors
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

import importlib

pyre_node_patched = importlib.import_module('isac.patch.pyre_patched.pyre_node')
pyre_node_original = importlib.import_module('pyre.pyre_node')
setattr(getattr(pyre_node_original, 'PyreNode'), 'recv_beacon', getattr(pyre_node_patched, 'recv_beacon'))

zbeacon_patched = importlib.import_module('isac.patch.pyre_patched.zbeacon')
zbeacon_original = importlib.import_module('pyre.zbeacon')
setattr(getattr(zbeacon_original, 'ZBeacon'), 'handle_pipe', getattr(zbeacon_patched, 'handle_pipe'))
setattr(getattr(zbeacon_original, 'ZBeacon'), 'send_beacon', getattr(zbeacon_patched, 'send_beacon'))
