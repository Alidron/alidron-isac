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
