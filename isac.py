
import logging

from .tools import green

from . import IsacNode, IsacValue

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    def p():
        green.sleep(0.1)

    def stop():
        n.shutdown()
        p()

    import sys
    n = IsacNode(sys.argv[1])

    @n.rpc_service.register(name='list')
    def list_():
        return n.rpc_service.procedures.keys()

    p()

    if sys.argv[1] == 'test01':
        val1 = IsacValue(n, 'this.is.a.test', 12)
    else:
        val1 = IsacValue(n, 'this.is.a.test')

    if sys.argv[1] == 'test02':
        val2 = IsacValue(n, 'this.is.another.test', 42)
    else:
        val2 = IsacValue(n, 'this.is.another.test')

    def notifyer(name, value, ts):
        print name, value, ts

    val1.observers += notifyer
    val2.observers += notifyer

    green.sleep(15)

    print val1
    print val2

    n.shutdown()
