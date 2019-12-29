# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports

# Third-party imports

# Local imports
from .concurrency import green


class Observable(set):

    def __call__(self, *args, **kwargs):
        for observer in self:
            green.spawn(observer, *args, **kwargs)

    def __iadd__(self, observer):
        self.add(observer)
        return self

    def __isub__(self, observer):
        self.remove(observer)
        return self
