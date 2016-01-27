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

import time
import threading
from inspect import getframeinfo, stack
from functools import wraps
from pprint import pformat as pf

from . import green

def spy_call(f, args=None, kwargs=None, with_thread=True, with_args=True, with_caller=True):
    frames = stack()
    try:
        print '>>>>>>', 'At', time.time(),

        if with_thread:
            print '; From thread', str(threading.current_thread()),
            try:
                g_run = green.getcurrent()._run
                print '; From greenlet %s.%s' % (g_run.__module__, g_run.__name__),
            except AttributeError:
                pass

        print '; Calling %s.%s.%s' % (f.__self__.__class__.__module__, f.__self__.__class__.__name__, f.__name__),

        if with_args:
            if args:
                print 'with args:', args,
            if kwargs:
                print 'and kwargs:', kwargs,

        if with_caller:
            caller = getframeinfo(frames[2][0])
            print '; Called by %s:%d (%s)' % (caller.filename, caller.lineno, caller.function),
    finally:
        del frames

def w_spy_call(f, **kwargs):
    @wraps(f)
    def _(*f_args, **f_kwargs):
        spy_call(f, f_args, f_kwargs, **kwargs)

        to_return = f(*f_args, **f_kwargs)

        if to_return is not None:
            print '; Returning', to_return,
        print

        return to_return

    return _

def spy_object(obj, class_=None, except_=None, **kwargs):
    if not class_:
        class_ = obj.__class__

    for m in dir(class_):
        if m.startswith('_') or m in except_:
            continue

        setattr(obj, m, w_spy_call(getattr(super(obj.__class__, obj), m), **kwargs))
