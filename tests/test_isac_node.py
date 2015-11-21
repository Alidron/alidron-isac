import logging
from isac import IsacNode

# logging.basicConfig(level=logging.DEBUG)

def test_creation():
    n = IsacNode('test')
    n.shutdown()

def test_2creation():
    n1 = IsacNode('A')
    n2 = IsacNode('B')

    try:
        assert n1.pyre.uuid() == n2.pyre.peers()[0]
        assert n2.pyre.uuid() == n1.pyre.peers()[0]
    finally:
        n1.shutdown()
        n2.shutdown()
