import logging
import pytest

from isac import IsacNode, IsacValue

# logging.basicConfig(level=logging.DEBUG)

def test_creation():
    nA = IsacNode('A')
    nB = IsacNode('B')

    try:
        ivA = IsacValue(nA, 'my_value')
        ivB = IsacValue(nB, 'my_value')
    finally:
        nA.shutdown()
        nB.shutdown()

@pytest.mark.xfail
def test_weakref():
    n = IsacNode('testtt')

    try:
        iv = IsacValue(n, 'test_iv')
        del iv
        assert n.isac_values.valuerefs() == []
    finally:
        n.shutdown()
