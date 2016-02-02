# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
from isac import IsacNode

# logging.basicConfig(level=logging.DEBUG)

def test_creation():
    n = IsacNode('test')
    n.shutdown()

def test_creation_double():
    n1 = IsacNode('A')
    n2 = IsacNode('B')

    try:
        assert n1.transport.uuid() == n2.transport.peers()[0]
        assert n2.transport.uuid() == n1.transport.peers()[0]
    finally:
        n1.shutdown()
        n2.shutdown()
