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
from datetime import datetime, timedelta
from random import randint

from isac import IsacNode, IsacValue, ArchivedValue, NoPeerWithHistoryException
from isac.tools import green, Observable

# logging.basicConfig(level=logging.DEBUG)

@pytest.fixture(scope='module')
def one_node(request):
    n = IsacNode('test')

    def teardown():
        n.shutdown()

    request.addfinalizer(teardown)
    return n

@pytest.fixture(scope='module')
def two_nodes(request):
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    def teardown():
        nA.shutdown()
        nB.shutdown()

    request.addfinalizer(teardown)
    return nA, nB

def test_creation_double():
    nA = IsacNode('A')
    nB = IsacNode('B')

    uri = 'test://test_isac_value/test_creation_double/my_value'
    try:
        ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
        ivB = IsacValue(nB, uri, survey_last_value=False, survey_static_tags=False)
    finally:
        nA.shutdown()
        nB.shutdown()

@pytest.mark.xfail
def test_weakref(one_node):
    iv = IsacValue(one_node, 'test://test_isac_value/test_weakref/test_iv', survey_last_value=False, survey_static_tags=False)
    del iv
    assert one_node.isac_values.valuerefs() == []

def test_creation_no_init(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_no_init/test_no_init'
    ivA = IsacValue(nA, uri, survey_static_tags=False)
    assert ivA.value is None
    assert ivA.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivA.static_tags == {}
    assert ivA.tags == {}
    assert ivA.metadata is None

    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivB.value is None
    assert ivB.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivB.static_tags == {}
    assert ivB.tags == {}
    assert ivB.metadata is None

    ivB = None
    ivA.value = randint(0, 100)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivB.value == ivA.value
    assert ivB.timestamp == ivA.timestamp
    assert ivB.static_tags == {}
    assert ivB.tags == nA.name_uuid()
    assert ivB.metadata is None

def test_creation_with_init(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_with_init/test_with_init'
    v = randint(0, 100)
    ivA = IsacValue(nA, uri, v, survey_last_value=False, survey_static_tags=False)
    assert ivA.value == v
    assert ivA.static_tags == {}
    assert ivA.tags == nA.name_uuid()
    assert ivA.metadata is None
    t = ivA.timestamp

    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivB.value == v
    assert ivB.timestamp == t
    assert ivB.static_tags == {}
    assert ivB.tags == nA.name_uuid()
    assert ivB.metadata is None

def test_creation_with_full_init(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_with_full_init/test_with_full_init'
    v1 = randint(0, 100)
    ts1 = datetime.now() - timedelta(hours=1)
    ivA = IsacValue(nA, uri, (v1, ts1), survey_last_value=False, survey_static_tags=False)
    assert ivA.value == v1
    assert ivA.timestamp == ts1
    assert ivA.static_tags == {}
    assert ivA.tags == nA.name_uuid()
    assert ivA.metadata is None

    v2 = v1 + 10
    ts2 = datetime.now() - timedelta(hours=2)
    ivB = IsacValue(nB, uri, (v2, ts2), survey_static_tags=False)
    assert ivB.value == v1
    assert ivB.timestamp == ts1
    assert ivB.static_tags == {}
    assert ivB.tags == nA.name_uuid()
    assert ivB.metadata is None
    assert ivA.value == v1
    assert ivA.timestamp == ts1
    assert ivA.static_tags == {}
    assert ivA.tags == nA.name_uuid()
    assert ivA.metadata is None

    ivB = None
    v3 = v2 + 10
    ts3 = datetime.now()
    ivB = IsacValue(nB, uri, (v3, ts3), survey_static_tags=False)
    assert ivB.value == v3
    assert ivB.timestamp == ts3
    assert ivB.static_tags == {}
    assert ivB.tags == nB.name_uuid()
    assert ivB.metadata is None
    assert ivA.value == v3
    assert ivA.timestamp == ts3
    assert ivA.static_tags == {}
    assert ivA.tags == nB.name_uuid()
    assert ivA.metadata is None

def test_creation_static_tags(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_static_tags/test_static_tags'
    static_tags = {'this': 'is', 'static': 'tags'}
    ivA = IsacValue(nA, uri, static_tags=static_tags, survey_last_value=False, survey_static_tags=False)
    assert ivA.static_tags == static_tags

    ivB = IsacValue(nB, uri, survey_last_value=False)
    assert ivB.static_tags == static_tags

    iv2A = IsacValue(nA, uri + '_dont_exists', survey_last_value=False)
    assert iv2A.static_tags == {}

def test_creation_dynamic_tags(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_dynamic_tags/test_dynamic_tags'

    dynamic_tags = {'this': 'is', 'dynamic': 'tags'}
    dynamic_tags_full = dynamic_tags
    dynamic_tags_full.update(nA.name_uuid())

    ivA = IsacValue(nA, uri, dynamic_tags=dynamic_tags, survey_last_value=False, survey_static_tags=False)
    assert ivA.tags == dynamic_tags

    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivB.tags == {} # Did not get stored because the default timestamps (0) were equal in both cases

    ivB = None
    ivA.value = randint(0, 100)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.tags == dynamic_tags_full
    assert ivB.value == ivA.value
    assert ivB.timestamp == ivA.timestamp
    assert ivB.tags == dynamic_tags_full

def test_creation_metadata(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_metadata/test_metadata'
    metadata = {'this': 'is', 'meta': 'data'}
    ivA = IsacValue(nA, uri, metadata=metadata, survey_last_value=False, survey_static_tags=False)
    assert ivA.metadata == metadata

    ivB = IsacValue(nB, uri, survey_last_value=False, survey_static_tags=False)
    assert ivB.metadata is None

    ivA.survey_metadata()
    assert ivA.metadata == metadata

    ivB.survey_metadata()
    assert ivB.metadata == metadata

def test_property_value(two_nodes):
    nA,nB = two_nodes

    uri = 'test://test_isac_value/test_property_value/test_property_value'
    ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.value is None
    assert ivB.value is None

    v1 = randint(0, 100)
    ivA.value = v1
    ts1 = ivA.timestamp
    assert ivA.value == v1
    assert ivB.value == v1

def test_property_timestamp(two_nodes):
    nA,nB = two_nodes

    uri = 'test://test_isac_value/test_property_timestamp/test_property_timestamp'
    ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivA.timestamp_float == 0
    assert ivB.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivB.timestamp_float == 0

    v1 = randint(0, 100)
    ivA.value = v1
    ts1 = ivA.timestamp
    assert datetime.fromtimestamp(ivA.timestamp_float) == ts1
    assert ivB.value == v1
    assert ivB.timestamp == ts1
    assert datetime.fromtimestamp(ivB.timestamp_float) == ts1

def test_property_value_ts(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_property_value_ts/test_property_value_ts'
    ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.value_ts == (None, datetime(1970, 1, 1, 0, 0))
    assert ivB.value_ts == (None, datetime(1970, 1, 1, 0, 0))

    v1 = randint(0, 100)
    ts1 = datetime.now() + timedelta(hours=1)
    ivA.value_ts = v1, ts1
    assert ivA.value_ts == (v1, ts1)
    assert ivA.value == v1
    assert datetime.fromtimestamp(ivA.timestamp_float) == ts1
    assert ivB.value_ts == (v1, ts1)
    assert ivB.value == v1
    assert ivB.timestamp == ts1
    assert datetime.fromtimestamp(ivB.timestamp_float) == ts1

# TODO: test_property_static_tags

def test_property_tags(two_nodes):
    nA,nB = two_nodes

    uri = 'test://test_isac_value/test_property_tags/test_property_tags'

    dynamic_tags = {'this': 'is', 'dynamic': 'tags'}
    dynamic_tags_full = dynamic_tags
    dynamic_tags_full.update(nA.name_uuid())

    dynamic_tags2 = {'this': 'is', 'dynamic': 'tags', 'additional': 'tag'}
    dynamic_tags2_full = dynamic_tags2
    dynamic_tags2_full.update(nA.name_uuid())

    ivA = IsacValue(nA, uri, randint(0, 100), dynamic_tags=dict(dynamic_tags), survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.tags == dynamic_tags_full
    assert ivB.tags == dynamic_tags_full

    ivA.tags['additional'] = 'tag'
    ivA.value = randint(0, 100)
    assert ivA.tags == dynamic_tags2_full
    assert ivB.tags == dynamic_tags2_full

def test_property_value_tags(two_nodes):
    nA,nB = two_nodes

    uri = 'test://test_isac_value/test_property_value_tags/test_property_value_tags'

    dynamic_tags = {'this': 'is', 'dynamic': 'tags'}
    dynamic_tags_full = dynamic_tags
    dynamic_tags_full.update(nA.name_uuid())

    dynamic_tags2 = {'this': 'is', 'dynamic': 'tags', 'additional': 'tag'}
    dynamic_tags2_full = dynamic_tags2
    dynamic_tags2_full.update(nA.name_uuid())

    ivA = IsacValue(nA, uri, randint(0, 100), dynamic_tags=dynamic_tags, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.value_tags == (ivA.value, dynamic_tags_full)
    assert ivB.value_tags == (ivA.value, dynamic_tags_full)

    v = randint(0, 100)
    ivA.value_tags = v, dynamic_tags2
    assert ivA.value_tags == (v, dynamic_tags2_full)
    assert ivB.value_tags == (v, dynamic_tags2_full)

def test_property_ts_tags(two_nodes):
    nA,nB = two_nodes

    uri = 'test://test_isac_value/test_property_ts_tags/test_property_ts_tags'

    dynamic_tags = {'this': 'is', 'dynamic': 'tags'}
    dynamic_tags_full = dynamic_tags
    dynamic_tags_full.update(nA.name_uuid())

    ivA = IsacValue(nA, uri, randint(0, 100), dynamic_tags=dynamic_tags, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.ts_tags == (ivA.timestamp, dynamic_tags_full)
    assert ivB.ts_tags == (ivA.timestamp, dynamic_tags_full)


def test_property_value_ts_tags(two_nodes):
    nA,nB = two_nodes

    uri = 'test://test_isac_value/test_property_value_ts_tags/test_property_value_ts_tags'

    dynamic_tags = {'this': 'is', 'dynamic': 'tags'}
    dynamic_tags_full = dynamic_tags
    dynamic_tags_full.update(nA.name_uuid())

    dynamic_tags2 = {'this': 'is', 'dynamic': 'tags', 'additional': 'tag'}
    dynamic_tags2_full = dynamic_tags2
    dynamic_tags2_full.update(nA.name_uuid())

    ivA = IsacValue(nA, uri, randint(0, 100), dynamic_tags=dynamic_tags, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.value_ts_tags == (ivA.value, ivA.timestamp, dynamic_tags_full)
    assert ivB.value_ts_tags == (ivA.value, ivA.timestamp, dynamic_tags_full)

    v = ivA.value + 10
    ts = ivA.timestamp + timedelta(hours=1)
    ivA.value_ts_tags = v, ts, dynamic_tags2
    assert ivA.value_ts_tags == (v, ts, dynamic_tags2_full)
    assert ivB.value_ts_tags == (v, ts, dynamic_tags2_full)

def test_property_metadata(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_property_metadata/test_property_metadata'
    ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, survey_static_tags=False)
    assert ivA.metadata is None
    assert ivB.metadata is None

    metadata = {'this': 'is', 'meta': 'data'}
    ivA.metadata = metadata
    assert ivA.metadata == metadata
    assert ivB.metadata is None

    ivB.survey_metadata()
    assert ivB.metadata == metadata

class Observer(object):

    def __init__(self):
        self.args = None

    def observer(self, *args):
        self.args = args
        self.static_tags = dict(args[0].static_tags)

def test_observer_after_creation(two_nodes):
    nA, nB = two_nodes
    obs = Observer()

    uri = 'test://test_isac_value/test_observer/test_observer'
    ivA = IsacValue(nA, uri, static_tags={'this': 'is', 'static': 'tags'}, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri)
    ivB.observers += obs.observer
    ivA.value = randint(0, 100)
    green.sleep(0.5)
    assert obs.args, 'Callback not received'
    iv_recv, value, ts, tags = obs.args
    assert iv_recv == ivB
    assert value == ivA.value
    assert ts == ivA.timestamp
    assert tags == ivA.tags
    assert obs.static_tags == ivA.static_tags

def test_observer_at_creation(two_nodes):
    nA, nB = two_nodes
    obs = Observer()

    uri = 'test://test_isac_value/test_observer_at_creation/test_observer'
    ivA = IsacValue(nA, uri, randint(0, 100), static_tags={'this': 'is', 'static': 'tags'}, survey_last_value=False, survey_static_tags=False)
    ivB = IsacValue(nB, uri, observers=Observable([obs.observer]))
    green.sleep(0.5)
    assert obs.args, 'Callback not received'
    iv_recv, value, ts, tags = obs.args
    assert iv_recv == ivB
    assert value == ivA.value
    assert ts == ivA.timestamp
    assert tags == ivA.tags
    assert obs.static_tags == ivA.static_tags

def test_observer_metadata(two_nodes):
    nA, nB = two_nodes
    obs = Observer()

    try:
        nB.transport.join_event() # Necesarry, but not user friendly
        uri = 'test://test_isac_value/test_observer_metadata/test_observer'
        ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
        ivB = IsacValue(nB, uri, survey_last_value=False, survey_static_tags=False)
        ivB.metadata_observers += obs.observer
        ivA.metadata = {'this': 'is', 'meta': 'data'}

        for i in range(10):
            green.sleep(0.5)
            if obs.args is not None:
                break

        assert obs.args, 'Callback not received'
        iv_recv, metadata, source_peer = obs.args
        assert iv_recv == ivB
        assert metadata == ivA.metadata
        assert source_peer['peer_name'] == nA.name
        assert source_peer['peer_uuid'] == str(nA.transport.uuid())

    finally:
        nB.transport.leave_event()

class FakeArchivedValue(ArchivedValue):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self._test_data = [
            (0, 10, {'peer_name': 'testA', 'peer_uuid': '123456'}),
            (1, 10.5, {'this': 'is', 'peer_name': 'testA', 'peer_uuid': '123456'}),
            (2, 11, {'a': 'tag', 'peer_name': 'testA', 'peer_uuid': '123456'}),
        ]
        self._test_time_period = None

    def get_history_impl(self, time_period):
        self._test_time_period = time_period
        return self._test_data

def test_history(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_history/test_history'
    ivA = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)
    ivB = FakeArchivedValue(nB, uri, survey_static_tags=False)
    time_period = (0, 20)
    data = ivA.get_history(time_period)
    data_fixture_converted = [(point[0], datetime.fromtimestamp(point[1]), point[2]) for point in ivB._test_data]
    assert ivB._test_time_period, 'History callback not called'
    assert ivB._test_time_period == list(time_period)
    assert data == data_fixture_converted

    with pytest.raises(NoPeerWithHistoryException):
        ivB.get_history(time_period)

# def test_create_many(two_nodes):
#     nA, nB = two_nodes
#
#     ivAs = []
#     ivBs = []
#     def notify_isac_value_entering(peer_name, uri):
#         iv = IsacValue(nB, str(uri))
#         iv.survey_metadata()
#         ivBs.append(iv)
#
#     nB.register_isac_value_entering(notify_isac_value_entering)
#
#     uri = 'test://test_isac_value/test_create_many/test'
#     metadata = {
#         'uri': uri,
#         'label': 'This is a test',
#         'help': 'You better know how it works!',
#         'max': 0,
#         'min': 65535,
#         'units': 'A',
#         'genre': 'metric',
#         'type': 'int',
#         'is_read_only': True,
#         'is_write_only': False,
#         'instance': 1,
#         'index': 0,
#         'value_id': 15646,
#         'node_id': 1,
#         'location': 'computer',
#         'home_id': '0xbeef',
#         'command_class': 'COMMMAND_CLASS_TEST',
#         'data_items': 'A short between 0 and 65535',
#     }
#     static_tags = {
#         'home_id': '0xbeef',
#         'location': 'computer',
#         'node_id': 1,
#         'command_class': 'COMMMAND_CLASS_TEST',
#         'index': 0,
#         'instance': 1,
#     },
#     for i in range(1000):
#         ivAs.append(IsacValue(nA, uri + str(i), i, static_tags=static_tags, metadata=metadata, survey_last_value=False, survey_static_tags=False))
#         green.sleep(0.010) # Needed otherwise some sockets does not close correctly and the test gets stuck...
#
#     green.sleep(1)
