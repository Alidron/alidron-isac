from random import randint

from isac import IsacNode, IsacValue

import logging

logging.basicConfig(level=logging.WARNING)

def test_survey_last_value():
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    try:
        iv = IsacValue(nA, 'my_value')

        # Uninitialised/new value have a None value at time 0
        assert nB.survey_last_value('my_value', limit_peers=1) == (None, 0)

        iv.value = randint(0, 100)
        assert nB.survey_last_value('my_value', limit_peers=1) == (iv.value, iv.timestamp_float)

        # Inexistent value are not an error, they simply return None at time 0
        # (That is actually what give the default state of an uninitialised/new value behind the scene)
        assert nB.survey_last_value('inexistent', limit_peers=1) == (None, 0)
    finally:
        nA.shutdown()
        nB.shutdown()

def test_survey_value_name():
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    try:
        iv1 = IsacValue(nA, 'iv1')
        iv2 = IsacValue(nA, 'iv2')

        assert nB.survey_value_name('', limit_peers=1) == set(['iv1', 'iv2'])
        assert nB.survey_value_name('i', limit_peers=1) == set(['iv1', 'iv2'])
        assert nB.survey_value_name('v', limit_peers=1) == set(['iv1', 'iv2'])
        assert nB.survey_value_name('1', limit_peers=1) == set(['iv1'])
        assert nB.survey_value_name('2', limit_peers=1) == set(['iv2'])
        assert nB.survey_value_name('^i', limit_peers=1) == set(['iv1', 'iv2'])
        assert nB.survey_value_name('[1|2]$', limit_peers=1) == set(['iv1', 'iv2'])
        assert nB.survey_value_name('^.*1', limit_peers=1) == set(['iv1'])
        assert nB.survey_value_name('^v', limit_peers=1) == set([])
        assert nB.survey_value_name('test', limit_peers=1) == set([])

        # Wrong RE should return an empty set AND not cause remote nodes to crash
        assert nB.survey_value_name('*', limit_peers=1) == set([])
        assert nB.survey_value_name('', limit_peers=1) == set(['iv1', 'iv2']), 'Remote node crashed'
    finally:
        nA.shutdown()
        nB.shutdown()

def test_survey_value_metadata():
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    try:
        iv_nometa = IsacValue(nA, 'iv_nometa')
        iv_meta = IsacValue(nA, 'iv_meta', metadata={'a': 1, 'b': 2})

        assert nB.survey_value_metadata('iv_nometa') is None
        assert nB.survey_value_metadata('iv_meta') == iv_meta.metadata
    finally:
        nA.shutdown()
        nB.shutdown()
