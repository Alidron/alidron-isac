# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports

# Third-party imports
import gevent as green  # noqa: F401
import zmq.green as zmq  # noqa: F401
from gevent.pool import Group as _Group, Pool as _Pool

# Local imports


class Future(green.Greenlet):
    """ A Gevent Greenlet providing the Future interface
    """

    def result(self, timeout=None):
        try:
            return self.get(timeout=timeout)
        except green.Timeout as e:
            raise TimeoutError(e)

    def exception(self, timeout=None):
        try:
            self.join(timeout=timeout)
        except green.Timeout as e:
            raise TimeoutError(e)
        return super(Future, self).exception

    def cancel(self):
        if not self.ready():
            self.kill()
        return True

    def cancelled(self):
        exc = super(Future, self).exception
        return self.ready() and isinstance(exc, green.GreenletExit)

    def running(self):
        return not self.done()

    def done(self):
        return self.ready()

    def add_done_callback(self, func):
        return self.link(func)


class Executor(object):
    """ An Executor using Gevent Group/Pool
    """

    def __init__(self, limit=None):
        self._limit = limit

        if limit is None:
            self._pool = _Group()
            self._pool.greenlet_class = Future
        else:
            self._pool = _Pool(size=limit, greenlet_class=Future)

    def submit(self, func, *args, **kw):
        pool = self._pool
        if pool is None:
            return
        return pool.spawn(func, *args, **kw)

    def wait(self, timeout=None):
        pool = self._pool
        if pool is None:
            return
        pool.join(timeout=timeout)
        num = len(pool.greenlets)
        if timeout is not None and num > 0:
            raise TimeoutError('%s tasks are still running' % num)

    def shutdown(self, wait=True, cancel=False):
        pool = self._pool
        self._pool = None

        if pool is None:
            return
        if cancel:
            pool.kill(block=True)
        if wait:
            pool.join()
