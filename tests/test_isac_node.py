# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import logging  # noqa: F401

# Third-party imports

# Local imports
from isac import IsacNode


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# pyre_logger = logging.getLogger('pyre')
# pyre_logger.setLevel(logging.DEBUG)
# pyre_logger.addHandler(logging.StreamHandler())
# pyre_logger.propagate = False


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
