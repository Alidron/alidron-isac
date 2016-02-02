# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import pytest

from isac import IsacNode


@pytest.fixture(scope='module')
def two_nodes(request):
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    def teardown():
        nA.shutdown()
        nB.shutdown()

    request.addfinalizer(teardown)
    return nA, nB

def test_isac_node(two_nodes):
    nA, nB = two_nodes

    spy = {}
    def my_func(*args, **kwargs):
        spy['args'] = args
        spy.update(kwargs)
        return 'fixture', 'data'

    uri = 'rpc://testA/my_func'
    published_uri = nA.add_rpc(my_func)
    assert published_uri == uri

    response = tuple(nB.call_rpc(uri, 1, 2, 3, a=4, b=5, c=6))
    assert response == ('fixture', 'data')
    assert spy['args'] == (1, 2, 3)
    assert spy['a'] == 4
    assert spy['b'] == 5
    assert spy['c'] == 6
