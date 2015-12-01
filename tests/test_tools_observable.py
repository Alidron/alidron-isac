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

from isac.tools import Observable, green

# logging.basicConfig(level=logging.DEBUG)

class Observer(object):
    def __init__(self):
        self.args = None
        self.kwargs = None

    def observer(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

def test_add():
    obs = Observable()
    o1 = Observer()
    o2 = Observer()

    assert not obs
    obs += o1.observer
    assert obs
    assert len(obs) == 1
    obs += o2.observer
    assert len(obs) == 2
    obs += o2.observer
    assert len(obs) == 2

def test_sub():
    obs = Observable()
    o1 = Observer()
    o2 = Observer()

    obs += o1.observer
    obs += o2.observer
    assert len(obs) == 2
    obs -= o1.observer
    assert len(obs) == 1
    obs -= o2.observer
    assert not obs

def test_call():
    obs = Observable()
    o1 = Observer()
    o2 = Observer()

    obs += o1.observer
    obs += o2.observer

    obs('arg1', 'arg2', arg3=3, arg4=4)
    green.sleep(0.1)
    assert o1.args == ('arg1', 'arg2')
    assert o1.kwargs == {'arg3': 3, 'arg4':4}
    assert o2.args == ('arg1', 'arg2')
    assert o2.kwargs == {'arg3': 3, 'arg4':4}

    obs()
    green.sleep(0.1)
    assert o1.args == ()
    assert o1.kwargs == {}
    assert o2.args == ()
    assert o2.kwargs == {}
