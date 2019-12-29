# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import time
import threading
from inspect import getframeinfo, stack
from functools import wraps
# from pprint import pformat as pf

# Third-party imports

# Local imports
from . import green


def spy_call(f, args=None, kwargs=None, with_thread=True, with_args=True, with_caller=True):
    frames = stack()
    try:
        print('>>>>>>', 'At', time.time(),)

        if with_thread:
            print('; From thread', str(threading.current_thread()),)
            try:
                g_run = green.getcurrent()._run
                print('; From greenlet %s.%s' % (g_run.__module__, g_run.__name__),)
            except AttributeError:
                pass

        print('; Calling %s.%s.%s' % (f.__self__.__class__.__module__,
                                      f.__self__.__class__.__name__, f.__name__),)

        if with_args:
            if args:
                print('with args:', args,)
            if kwargs:
                print('and kwargs:', kwargs,)

        if with_caller:
            caller = getframeinfo(frames[2][0])
            print('; Called by %s:%d (%s)' % (caller.filename, caller.lineno, caller.function),)
    finally:
        del frames


def w_spy_call(f, **kwargs):
    @wraps(f)
    def _(*f_args, **f_kwargs):
        spy_call(f, f_args, f_kwargs, **kwargs)

        to_return = f(*f_args, **f_kwargs)

        if to_return is not None:
            print('; Returning', to_return,)
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
