# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import logging  # noqa: F401
import time
from random import randint

# Third-party imports

# Local imports
from isac import IsacValue, ArchivedValue
from isac.tools.tests import m_two_nodes as two_nodes  # noqa: F401

# logging.basicConfig(level=logging.DEBUG)


def test_survey_last_value(two_nodes):  # noqa: F811
    nA, nB = two_nodes

    uri = 'test://test_survey_value/test_survey_last_value/my_value'
    iv = IsacValue(nA, uri, survey_last_value=False, survey_static_tags=False)

    # Uninitialised/new value have a None value at time 0
    assert nB.survey_last_value(uri, limit_peers=1) == (None, 0, {})

    iv.value = randint(0, 100)
    assert nB.survey_last_value(
        uri, limit_peers=1) == (iv.value, iv.timestamp_float, nA.name_uuid())

    # Inexistent value are not an error, they simply return None at time 0
    # (That is actually what give the default state of an uninitialised/new value behind the scene)
    assert nB.survey_last_value(
        'test://test_survey_value/test_survey_last_value/inexistent',
        limit_peers=1
    ) == (None, 0, {})


def test_survey_value_uri(two_nodes):  # noqa: F811
    nA, nB = two_nodes

    iv1 = IsacValue(nA, 'iv1', survey_last_value=False, survey_static_tags=False)
    iv2 = IsacValue(nA, 'iv2', survey_last_value=False, survey_static_tags=False)

    assert nB.survey_value_uri('', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_uri('i', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_uri('v', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_uri('1', limit_peers=1) >= set(['iv1'])
    assert nB.survey_value_uri('2', limit_peers=1) >= set(['iv2'])
    assert nB.survey_value_uri('^i', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_uri('[1|2]$', limit_peers=1) >= set(['iv1', 'iv2'])
    assert nB.survey_value_uri('^.*1', limit_peers=1) >= set(['iv1'])
    assert nB.survey_value_uri('^v', limit_peers=1, timeout=0.1) == set([])
    assert nB.survey_value_uri('nothing', limit_peers=1, timeout=0.1) == set([])

    # Wrong RE should return an empty set AND not cause remote nodes to crash
    assert nB.survey_value_uri('*', limit_peers=1, timeout=0.1) == set([])
    assert nB.survey_value_uri('', limit_peers=1) >= set(['iv1', 'iv2']), 'Remote node crashed'


def test_survey_value_static_tags(two_nodes):  # noqa: F811
    nA, nB = two_nodes

    uri_nostatictags = 'test://test_survey_value/test_survey_value_static_tags/iv_nostatictags'
    iv_nostatictags = IsacValue(
        nA, uri_nostatictags, survey_last_value=False, survey_static_tags=False)
    uri_statictags = 'test://test_survey_value/test_survey_value_static_tags/iv_statictags'
    iv_statictags = IsacValue(
        nA, uri_statictags, static_tags={'this': 'is', 'static': 'tags'},
        survey_last_value=False, survey_static_tags=False
    )

    assert nB.survey_value_static_tags(uri_nostatictags, timeout=0.1) == {}
    assert nB.survey_value_static_tags(
        'test://test_survey_value/test_survey_value_static_tags/unknown', timeout=0.1) == {}
    assert nB.survey_value_static_tags(uri_statictags) == iv_statictags.static_tags


def test_survey_value_metadata(two_nodes):  # noqa: F811
    nA, nB = two_nodes

    uri_nometa = 'test://test_survey_value/test_survey_value_metadata/iv_nometa'
    iv_nometa = IsacValue(nA, uri_nometa, survey_last_value=False, survey_static_tags=False)
    uri_meta = 'test://test_survey_value/test_survey_value_metadata/iv_meta'
    iv_meta = IsacValue(
        nA, uri_meta, metadata={'a': 1, 'b': 2},
        survey_last_value=False, survey_static_tags=False
    )

    assert nB.survey_value_metadata(uri_nometa, timeout=0.1) == (None, None)
    assert nB.survey_value_metadata(
        'test://test_survey_value/test_survey_value_metadata/unknown', timeout=0.1) == (None, None)
    assert nB.survey_value_metadata(uri_meta) == (iv_meta.metadata, nA.name_uuid())


def test_survey_values_metadata(two_nodes):  # noqa: F811
    nA, nB = two_nodes

    uri_nometa = 'test://test_survey_value/test_survey_values_metadata/iv_nometa'
    iv_nometa = IsacValue(nA, uri_nometa, survey_last_value=False, survey_static_tags=False)
    uri_meta1 = 'test://test_survey_value/test_survey_value_metadata/iv_meta1'
    iv_meta1 = IsacValue(
        nA, uri_meta1, metadata={'a': 1, 'b': 2}, survey_last_value=False, survey_static_tags=False)
    uri_meta2 = 'test://test_survey_value/test_survey_value_metadata/iv_meta2'
    iv_meta2 = IsacValue(
        nA, uri_meta2, metadata={'c': 3, 'd': 4}, survey_last_value=False, survey_static_tags=False)

    assert nB.survey_values_metadata([uri_meta1]) == {uri_meta1: iv_meta1.metadata}
    assert nB.survey_values_metadata([uri_meta1, uri_meta2]) == {
        uri_meta1: iv_meta1.metadata,
        uri_meta2: iv_meta2.metadata,
    }
    assert nB.survey_values_metadata('.*meta.$', is_re=True) == {
        uri_meta1: iv_meta1.metadata,
        uri_meta2: iv_meta2.metadata,
    }
    assert nB.survey_values_metadata('.*nometa$', is_re=True, timeout=0.1) == {}
    assert nB.survey_values_metadata(
        'test://test_survey_value/test_survey_value_metadata/unknown', timeout=0.1) == {}

    # Wrong RE should return an empty set AND not cause remote nodes to crash
    assert nB.survey_values_metadata('*', is_re=True, timeout=0.1) == {}
    assert nB.survey_values_metadata(
        [uri_meta1]) == {uri_meta1: iv_meta1.metadata}, 'Remote node crashed'


def test_survey_value_history(two_nodes):  # noqa: F811
    nA, nB = two_nodes
    time_period = (time.time()-86400, time.time())

    uri_arch = 'test://test_survey_value/test_survey_value_history/archived_iv'
    archived_iv = ArchivedValue(nA, uri_arch, survey_last_value=False, survey_static_tags=False)
    uri_simple = 'test://test_survey_value/test_survey_value_history/simple_iv'
    simple_iv = IsacValue(nA, uri_simple, survey_last_value=False, survey_static_tags=False)

    assert nB.survey_value_history(uri_simple, (0, 1000), timeout=0.1) is None
    assert nB.survey_value_history(uri_arch, (0, 1000)) == b'testA'
    assert nB.survey_value_history(
        'test://test_survey_value/test_survey_value_history/unknown',
        (0, 1000), timeout=0.1
    ) is None
