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
import time
from random import randint

from isac import IsacNode, IsacValue, ArchivedValue

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

def test_survey_last_value(two_nodes):
    nA, nB = two_nodes

    uri = 'test://test_survey_value/test_survey_last_value/my_value'
    iv = IsacValue(nA, uri)

    # Uninitialised/new value have a None value at time 0
    assert nB.survey_last_value(uri, limit_peers=1) == (None, 0)

    iv.value = randint(0, 100)
    assert nB.survey_last_value(uri, limit_peers=1) == (iv.value, iv.timestamp_float)

    # Inexistent value are not an error, they simply return None at time 0
    # (That is actually what give the default state of an uninitialised/new value behind the scene)
    assert nB.survey_last_value('test://test_survey_value/test_survey_last_value/inexistent', limit_peers=1) == (None, 0)

def test_survey_value_name(two_nodes):
    nA, nB = two_nodes

    iv1 = IsacValue(nA, 'iv1')
    iv2 = IsacValue(nA, 'iv2')

    assert nB.survey_value_name('', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_name('i', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_name('v', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_name('1', limit_peers=1) >= set(['iv1'])
    assert nB.survey_value_name('2', limit_peers=1) >= set(['iv2'])
    assert nB.survey_value_name('^i', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_name('[1|2]$', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_name('^.*1', limit_peers=1) >= set(['iv1'])
    assert nB.survey_value_name('^v', limit_peers=1) == set([])
    assert nB.survey_value_name('nothing', limit_peers=1) == set([])

    # Wrong RE should return an empty set AND not cause remote nodes to crash
    assert nB.survey_value_name('*', limit_peers=1) == set([])
    assert nB.survey_value_name('', limit_peers=1) >= set(['iv1', 'iv2']), 'Remote node crashed'

def test_survey_value_metadata(two_nodes):
    nA, nB = two_nodes

    uri_nometa = 'test://test_survey_value/test_survey_value_metadata/iv_nometa'
    iv_nometa = IsacValue(nA, uri_nometa)
    uri_meta = 'test://test_survey_value/test_survey_value_metadata/iv_meta'
    iv_meta = IsacValue(nA, uri_meta, metadata={'a': 1, 'b': 2})

    assert nB.survey_value_metadata(uri_nometa) is None
    assert nB.survey_value_metadata('test://test_survey_value/test_survey_value_metadata/unknown') is None
    assert nB.survey_value_metadata(uri_meta) == iv_meta.metadata

def test_survey_values_metadata(two_nodes):
    nA, nB = two_nodes

    uri_nometa = 'test://test_survey_value/test_survey_values_metadata/iv_nometa'
    iv_nometa = IsacValue(nA, uri_nometa)
    uri_meta1 = 'test://test_survey_value/test_survey_value_metadata/iv_meta1'
    iv_meta1 = IsacValue(nA, uri_meta1, metadata={'a': 1, 'b': 2})
    uri_meta2 = 'test://test_survey_value/test_survey_value_metadata/iv_meta2'
    iv_meta2 = IsacValue(nA, uri_meta2, metadata={'c': 3, 'd': 4})

    assert nB.survey_values_metadata([uri_meta1]) == {uri_meta1: iv_meta1.metadata}
    assert nB.survey_values_metadata([uri_meta1, uri_meta2]) == {
        uri_meta1: iv_meta1.metadata,
        uri_meta2: iv_meta2.metadata,
    }
    assert nB.survey_values_metadata('.*meta.$', is_re=True) == {
        uri_meta1: iv_meta1.metadata,
        uri_meta2: iv_meta2.metadata,
    }
    assert nB.survey_values_metadata('.*nometa$', is_re=True) == {}
    assert nB.survey_values_metadata('test://test_survey_value/test_survey_value_metadata/unknown') == {}

    # Wrong RE should return an empty set AND not cause remote nodes to crash
    assert nB.survey_values_metadata('*', is_re=True) == {}
    assert nB.survey_values_metadata([uri_meta1]) == {uri_meta1: iv_meta1.metadata}, 'Remote node crashed'

def test_survey_value_history(two_nodes):
    nA, nB = two_nodes
    time_period = (time.time()-86400, time.time())

    uri_arch = 'test://test_survey_value/test_survey_value_history/archived_iv'
    archived_iv = ArchivedValue(nA, uri_arch)
    uri_simple = 'test://test_survey_value/test_survey_value_history/simple_iv'
    simple_iv = IsacValue(nA, uri_simple)

    assert nB.survey_value_history(uri_simple, (0, 1000)) is None
    assert nB.survey_value_history(uri_arch, (0, 1000)) == 'testA'
    assert nB.survey_value_history('test://test_survey_value/test_survey_value_history/unknown', (0, 1000)) is None
