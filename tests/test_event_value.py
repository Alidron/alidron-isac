# Copyright 2015 - Alidron's authors
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

from isac import IsacNode, IsacValue
from isac.tools import green

# logging.basicConfig(level=logging.DEBUG)

@pytest.fixture(scope='module')
def two_nodes(request):
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    def teardown():
        nA.shutdown()
        nB.shutdown()

    request.addfinalizer(teardown)
    return nA, nB

class Observer(object):

    def __init__(self):
        self.args = None

    def callback(self, *args):
        self.args = args

def test_isac_value_entering_event(two_nodes):
    nA, nB = two_nodes
    obs = Observer()

    nB.register_isac_value_entering(obs.callback)
    uri = 'test://test_event_value/test_isac_value_entering_event/test'
    nA.event_isac_value_entering(uri)

    green.sleep(0.25)

    assert obs.args, 'Callback not called'
    assert obs.args == ('testA', uri)

    nB.unregister_isac_value_entering(obs.callback)
    nA.event_isac_value_entering(uri + '2')

    green.sleep(0.25)

    assert obs.args == ('testA', uri)

class FakeIsacValue(object):

    def __init__(self):
        self.metadata = None

    def _set_metadata(self, metadata):
        self.metadata = metadata

def test_value_metadata_update_event(two_nodes):
    nA, nB = two_nodes
    fake_iv = FakeIsacValue()
    nB.transport.join_event()

    green.sleep(0.25)

    uri = 'test://test_event_value/test_value_metadata_update_event/test'
    nB.isac_values[uri] = fake_iv
    nA.event_value_metadata_update(uri, {'this is': 'metadata'})

    green.sleep(0.25)

    assert fake_iv.metadata, 'Callback not called'
    assert fake_iv.metadata == {'this is': 'metadata'}
