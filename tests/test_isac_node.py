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
from isac import IsacNode

# logging.basicConfig(level=logging.DEBUG)

def test_creation():
    n = IsacNode('test')
    n.shutdown()

def test_creation_double():
    n1 = IsacNode('A')
    n2 = IsacNode('B')

    try:
        assert n1.transport.uuid() == n2.transport.peers()[0]
        assert n2.transport.uuid() == n1.transport.peers()[0]
    finally:
        n1.shutdown()
        n2.shutdown()
