# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
