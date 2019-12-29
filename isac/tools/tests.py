# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports

# Third-party imports
import pytest

# Local imports
from isac import IsacNode


def _one_node():
    n = IsacNode('test')
    yield n
    n.shutdown()


@pytest.fixture(scope='function')
def f_one_node():
    yield from _one_node()


@pytest.fixture(scope='module')
def m_one_node():
    yield from _one_node()


def _two_nodes():
    nA = IsacNode('testA')
    nB = IsacNode('testB')
    yield nA, nB
    nA.shutdown()
    nB.shutdown()


@pytest.fixture(scope='function')
def f_two_nodes():
    yield from _two_nodes()


@pytest.fixture(scope='module')
def m_two_nodes():
    yield from _two_nodes()
