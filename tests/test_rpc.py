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
