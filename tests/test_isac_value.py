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
from isac.tools import green

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
        ivA = IsacValue(nA, uri)
        ivB = IsacValue(nB, uri)
    finally:
        nA.shutdown()
        nB.shutdown()

@pytest.mark.xfail
def test_weakref(one_node):
    iv = IsacValue(one_node, 'test://test_isac_value/test_weakref/test_iv')
    del iv
    assert one_node.isac_values.valuerefs() == []

def test_creation_no_init(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_no_init/test_no_init'
    ivA = IsacValue(nA, uri)
    assert ivA.value == None
    assert ivA.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivA.metadata == None

    ivA.value = randint(0, 100)
    ivB = IsacValue(nB, uri)
    assert ivB.value == ivA.value
    assert ivB.timestamp == ivA.timestamp
    assert ivB.metadata == None

def test_creation_with_init(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_with_init/test_with_init'
    v = randint(0, 100)
    ivA = IsacValue(nA, uri, v)
    assert ivA.value == v
    assert ivA.metadata == None
    t = ivA.timestamp

    ivB = IsacValue(nB, uri)
    assert ivB.value == v
    assert ivB.timestamp == t
    assert ivB.metadata == None

def test_creation_with_full_init(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_with_full_init/test_with_full_init'
    v1 = randint(0, 100)
    ts1 = datetime.now() - timedelta(hours=1)
    ivA = IsacValue(nA, uri, (v1, ts1))
    assert ivA.value == v1
    assert ivA.timestamp == ts1
    assert ivA.metadata == None

    v2 = v1 + 10
    ts2 = datetime.now() - timedelta(hours=2)
    ivB = IsacValue(nB, uri, (v2, ts2))
    assert ivB.value == v1
    assert ivB.timestamp == ts1
    assert ivB.metadata == None
    assert ivA.value == v1
    assert ivA.timestamp == ts1
    assert ivA.metadata == None

    ivB = None
    v3 = v2 + 10
    ts3 = datetime.now()
    ivB = IsacValue(nB, uri, (v3, ts3))
    assert ivB.value == v3
    assert ivB.timestamp == ts3
    assert ivB.metadata == None
    assert ivA.value == v3
    assert ivA.timestamp == ts3
    assert ivA.metadata == None

def test_creation_metadata(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_creation_metadata/test_metadata'
    metadata = {'this': 'is', 'meta': 'data'}
    ivA = IsacValue(nA, uri, metadata=metadata)
    assert ivA.value == None
    assert ivA.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivA.metadata == metadata

    ivB = IsacValue(nB, uri)
    assert ivB.value == None
    assert ivB.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivB.metadata == None

    ivA.survey_metadata()
    assert ivA.metadata == metadata

    ivB.survey_metadata()
    assert ivB.metadata == metadata

def test_property_value_ts(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_property_value_ts/test_property_value_ts'
    ivA = IsacValue(nA, uri)
    ivB = IsacValue(nB, uri)
    assert ivA.value == None
    assert ivA.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivA.timestamp_float == 0
    assert ivA.value_ts == (None, datetime(1970, 1, 1, 0, 0))
    assert ivB.value == None
    assert ivB.timestamp == datetime(1970, 1, 1, 0, 0)
    assert ivB.timestamp_float == 0
    assert ivB.value_ts == (None, datetime(1970, 1, 1, 0, 0))

    v1 = randint(0, 100)
    ivA.value = v1
    ts1 = ivA.timestamp
    assert ivA.value == v1
    assert datetime.fromtimestamp(ivA.timestamp_float) == ts1
    assert ivA.value_ts == (v1, ts1)
    assert ivB.value == v1
    assert ivB.timestamp == ts1
    assert datetime.fromtimestamp(ivB.timestamp_float) == ts1
    assert ivB.value_ts == (v1, ts1)

    v2 = v1 + 10
    ts2 = ts1 + timedelta(hours=1)
    ivA.value_ts = v2, ts2
    assert ivA.value == v2
    assert datetime.fromtimestamp(ivA.timestamp_float) == ts2
    assert ivA.value_ts == (v2, ts2)
    assert ivB.value == v2
    assert ivB.timestamp == ts2
    assert datetime.fromtimestamp(ivB.timestamp_float) == ts2
    assert ivB.value_ts == (v2, ts2)

def test_property_metadata(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_property_metadata/test_property_metadata'
    ivA = IsacValue(nA, uri)
    ivB = IsacValue(nB, uri)
    assert ivA.metadata == None
    assert ivB.metadata == None

    metadata = {'this': 'is', 'meta': 'data'}
    ivA.metadata = metadata
    assert ivA.metadata == metadata
    assert ivB.metadata == None

    ivB.survey_metadata()
    assert ivB.metadata == metadata

class Observer(object):

    def __init__(self):
        self.args = None

    def observer(self, *args):
        self.args = args

def test_observer(two_nodes):
    nA, nB = two_nodes
    obs = Observer()

    uri = 'test://test_isac_value/test_observer/test_observer'
    ivA = IsacValue(nA, uri)
    ivB = IsacValue(nB, uri)
    ivB.observers += obs.observer
    ivA.value = randint(0, 100)
    green.sleep(0.5)
    assert obs.args, 'Callback not received'
    uri_recv, value, ts = obs.args
    assert uri_recv == uri
    assert value == ivA.value
    assert ts == ivA.timestamp

class FakeArchivedValue(ArchivedValue):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self._test_data = [(0, 10), (1, 10.5), (2, 11),]
        self._test_time_period = None

    def get_history_impl(self, time_period):
        self._test_time_period = time_period
        return self._test_data

def test_history(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_isac_value/test_history/test_history'
    ivA = IsacValue(nA, uri)
    ivB = FakeArchivedValue(nB, uri)
    time_period = (0, 20)
    data = ivA.get_history(time_period)
    data_fixture_converted = [(point[0], datetime.fromtimestamp(point[1])) for point in ivB._test_data]
    assert ivB._test_time_period, 'History callback not called'
    assert ivB._test_time_period == list(time_period)
    assert data == data_fixture_converted

    with pytest.raises(NoPeerWithHistoryException):
        ivB.get_history(time_period)
