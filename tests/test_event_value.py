# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import pytest

from isac import IsacNode
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
        self.source_peer = None

    def _set_metadata(self, metadata, source_peer):
        self.metadata = metadata
        self.source_peer = source_peer

def test_value_metadata_update_event(two_nodes):
    nA, nB = two_nodes
    fake_iv = FakeIsacValue()
    nB.transport.join_event()

    green.sleep(0.25)

    uri = 'test://test_event_value/test_value_metadata_update_event/test'
    nB.isac_values[uri] = fake_iv
    nA.event_value_metadata_update(uri, {'this is': 'metadata'}, nA.name_uuid())

    green.sleep(0.25)

    assert fake_iv.metadata, 'Callback not called'
    assert fake_iv.metadata == {'this is': 'metadata'}
    assert fake_iv.source_peer['peer_name'] == nA.name
    assert fake_iv.source_peer['peer_uuid'] == str(nA.transport.uuid())
