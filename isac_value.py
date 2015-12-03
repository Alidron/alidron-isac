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
import time
from datetime import datetime

from .tools import green, Observable

logger = logging.getLogger(__name__)

class IsacValue(object):

    def __init__(self, isac_node, uri, initial_value=None, metadata=None, observers=Observable()):
        ts = datetime.now()

        self.isac_node = isac_node
        self.uri = uri
        self._metadata = metadata
        self.observers = observers
        self.metadata_observers = Observable()

        self.isac_node.rpc.register(
            lambda: (self._value, self.timestamp_float),
            name=self.uri
        )

        self._value = initial_value
        if initial_value is None:
            self._value, self._timestamp = None, datetime.fromtimestamp(0)
            self.update_value_from_isac(*self.isac_node.survey_last_value(self.uri, limit_peers=1))
        elif isinstance(initial_value, tuple):
            last_value, last_ts_float = self.isac_node.survey_last_value(self.uri, limit_peers=1)

            if isinstance(initial_value[1], datetime):
                last_ts = datetime.fromtimestamp(last_ts_float)
            else:
                last_ts = last_ts_float

            if initial_value[1] > last_ts: # We want to publish our last value to anyone outside
                logger.debug('publishing former value', initial_value)
                self.value_ts = initial_value
            else: # We want to notify all our internal subscribers of the newer last value
                self._value, self._timestamp = None, datetime.fromtimestamp(0)
                self.update_value_from_isac(last_value, last_ts_float)
        else:
            logger.debug('publishing value', initial_value)
            self.value_ts = initial_value, ts

        #print '>>>>>', self.uri, id(self), type(self._metadata), self._metadata
        if self._metadata:
            self.isac_node.event_value_metadata_update(self.uri, self._metadata)

        self.isac_node.subscribe(self.uri, self)

        self.isac_node.event_isac_value_entering(self.uri)

    def __del__(self):
        self.isac_node.rpc.unregister(self.uri)

    @property
    def value(self):
        green.sleep(0.001)
        return self._value

    @value.setter
    def value(self, new_value):
        ts = datetime.now()
        self._value = new_value
        self._timestamp = ts
        self.publish_value(self._value, self._timestamp)

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def timestamp_float(self):
        return time.mktime(self._timestamp.timetuple()) + (self._timestamp.microsecond / 1000000.0)

    @property
    def value_ts(self):
        return self._value, self._timestamp

    @value_ts.setter
    def value_ts(self, args):
        value, ts = args
        self._value = value
        if isinstance(ts, datetime):
            self._timestamp = ts
        else:
            self._timestamp = datetime.fromtimestamp(ts)

        self.publish_value(self._value, self._timestamp)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata
        self.isac_node.event_value_metadata_update(self.uri, self._metadata)

    def _set_metadata(self, metadata):
        if not metadata:
            return

        self._metadata = metadata
        if self._metadata:
            self.metadata_observers(self.uri, self._metadata)

    def update_value_from_isac(self, new_value, ts_float):
        if ts_float > self.timestamp_float:
            self._value = new_value
            self._timestamp = datetime.fromtimestamp(ts_float)
            self.observers(self.uri, self._value, self._timestamp)
        elif ts_float < self.timestamp_float:
            logger.warning('Trying to update value %s with a value older than what we have (%f vs. %f)', self.uri, ts_float, self.timestamp_float)
        # else equal time => do nothing

    def publish_value(self, value, ts):
        ts_float = self.timestamp_float
        logger.info('Publishing for %s: %s, %s', self.uri, value, ts_float)
        self.isac_node.pub_sub.publish(self.uri, (value, ts_float))

    def survey_metadata(self):
        self._set_metadata(self.isac_node.survey_value_metadata(self.uri))

    def get_history(self, time_period):
        peer_name = self.isac_node.survey_value_history(self.uri, time_period)
        if not peer_name:
            raise NoPeerWithHistoryException('Could not find any peer that could provide history for %s' % self.uri)

        t1, t2 = time_period
        if isinstance(t1, datetime):
            t1 = time.mktime(t1.timetuple()) + (t1.microsecond * 1e-6)
        if isinstance(t2, datetime):
            t2 = time.mktime(t2.timetuple()) + (t2.microsecond * 1e-6)

        func_name = '.'.join((self.uri, 'get_history_impl'))
        data = self.isac_node.rpc.call_on(peer_name, func_name, (t1, t2))
        return [(point[0], datetime.fromtimestamp(point[1])) for point in data]

    def __str__(self):
        return '{0}: {1}'.format(self.timestamp, self.value)

class ArchivedValue(IsacValue):

    def __init__(self, *args, **kwargs):
        super(ArchivedValue, self).__init__(*args, **kwargs)

        self.isac_node.rpc.register(
            self.get_history_impl,
            name='.'.join((self.uri, 'get_history_impl'))
        )

    def get_history_impl(self, time_period):
        return []

class NoPeerWithHistoryException(Exception):
    pass
