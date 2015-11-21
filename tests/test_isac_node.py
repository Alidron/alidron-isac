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
        assert n1.transport.uuid() == n2.transport.peers()[0]
        assert n2.transport.uuid() == n1.transport.peers()[0]
    finally:
        n1.shutdown()
        n2.shutdown()
