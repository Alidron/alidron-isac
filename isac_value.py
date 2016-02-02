# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import time
from datetime import datetime

from .tools import green, Observable

logger = logging.getLogger(__name__)

class IsacValue(object):

    def __init__(self, isac_node, uri, initial_value=None, static_tags=None, dynamic_tags=None, metadata=None, observers=None, survey_last_value=True, survey_static_tags=True):
        ts = datetime.now()

        self.isac_node = isac_node
        self.uri = uri
        self._metadata = metadata
        self.observers = Observable() if observers is None else observers
        self._static_tags = {} if static_tags is None else static_tags
        self._dynamic_tags = {} if dynamic_tags is None else dynamic_tags
        self.metadata_observers = Observable()

        self.isac_node.rpc.register(
            lambda: (self._value, self.timestamp_float),
            name=self.uri
        )

        if not self._static_tags and survey_static_tags:
            self._static_tags = self.isac_node.survey_value_static_tags(self.uri)

        self._value = initial_value
        if initial_value is None:
            self._value, self._timestamp = None, datetime.fromtimestamp(0)
            if survey_last_value:
                self.update_value_from_isac(*self.isac_node.survey_last_value(self.uri, limit_peers=1))

        elif isinstance(initial_value, tuple):
            if not survey_last_value:
                self.value_ts = initial_value

            else:
                last_value, last_ts_float, tags = self.isac_node.survey_last_value(self.uri, limit_peers=1)

                if isinstance(initial_value[1], datetime):
                    last_ts = datetime.fromtimestamp(last_ts_float)
                else:
                    last_ts = last_ts_float

                if initial_value[1] > last_ts: # We want to publish our last value to anyone outside
                    logger.debug('(%s, %s) publishing former value: %s', self.isac_node.name, self.uri, initial_value)
                    self.value_ts = initial_value
                else: # We want to notify all our internal subscribers of the newer last value
                    self._value, self._timestamp = None, datetime.fromtimestamp(0)
                    self.update_value_from_isac(last_value, last_ts_float, tags)

        else:
            logger.debug('(%s, %s) publishing value: %s', self.isac_node.name, self.uri, initial_value)
            self.value_ts = initial_value, ts

        #print '>>>>>', self.uri, id(self), type(self._metadata), self._metadata
        if self._metadata:
            self.isac_node.event_value_metadata_update(self.uri, self._metadata, self.isac_node.name_uuid())

        self.isac_node.subscribe(self.uri, self)

        self.isac_node.event_isac_value_entering(self.uri)

    def __del__(self):
        self.isac_node.rpc.unregister(self.uri)

    ### Value property

    @property
    def value(self):
        green.sleep(0.001)
        return self._value

    @value.setter
    def value(self, new_value):
        ts = datetime.now()
        self._value = new_value
        self._timestamp = ts
        self.publish_value(self._value, self._timestamp, self._dynamic_tags)

    ### TS property

    @property
    def timestamp(self):
        green.sleep(0.001)
        return self._timestamp

    @property
    def timestamp_float(self):
        green.sleep(0.001)
        return time.mktime(self._timestamp.timetuple()) + (self._timestamp.microsecond / 1000000.0)

    ### Value/TS property

    @property
    def value_ts(self):
        green.sleep(0.001)
        return self._value, self._timestamp

    @value_ts.setter
    def value_ts(self, args):
        value, ts = args
        self._value = value
        if isinstance(ts, datetime):
            self._timestamp = ts
        else:
            self._timestamp = datetime.fromtimestamp(ts)

        self.publish_value(self._value, self._timestamp, self._dynamic_tags)

    ### Static tags property

    @property
    def static_tags(self):
        return self._static_tags

    ### Dynamic tags property

    @property
    def tags(self):
        green.sleep(0.001)
        return self._dynamic_tags

    @tags.setter
    def tags(self, tags):
        self._dynamic_tags = tags

    ### Value/Dynamic tags property

    @property
    def value_tags(self):
        green.sleep(0.001)
        return self._value, self._dynamic_tags

    @value_tags.setter
    def value_tags(self, args):
        value, tags = args
        self._dynamic_tags = tags
        self.value = value

    ### TS/Dynamic tags property

    @property
    def ts_tags(self):
        green.sleep(0.001)
        return self._timestamp, self._dynamic_tags

    ### Value/TS/Dynamic tags property

    @property
    def value_ts_tags(self):
        green.sleep(0.001)
        return self._value, self._timestamp, self._dynamic_tags

    @value_ts_tags.setter
    def value_ts_tags(self, args):
        value, ts, tags = args
        self._dynamic_tags = tags
        self.value_ts = value, ts

    ### Metadata property

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata
        self.isac_node.event_value_metadata_update(self.uri, self._metadata, self.isac_node.name_uuid())

    def _set_metadata(self, metadata, source_peer):
        if not metadata:
            return

        self._metadata = metadata
        if self._metadata:
            self.metadata_observers(self, self._metadata, source_peer)

    def update_value_from_isac(self, new_value, ts_float, tags):
        if ts_float > self.timestamp_float:
            logger.debug('(%s, %s) Got newer value: %s, %s, %s', self.isac_node.name, self.uri, new_value, ts_float, tags)
            self._value = new_value
            self._timestamp = datetime.fromtimestamp(ts_float)
            self._dynamic_tags = tags
            self.observers(self, self._value, self._timestamp, self._dynamic_tags)
        elif ts_float < self.timestamp_float:
            logger.warning('(%s, %s) Trying to update value with a value older than what we have (%f vs. %f)', self.isac_node.name, self.uri, ts_float, self.timestamp_float)
        # else equal time => do nothing

    def publish_value(self, value, ts, tags):
        ts_float = self.timestamp_float
        tags.update(self.isac_node.name_uuid())

        logger.debug('(%s, %s) Publishing: %s, %s, %s', self.isac_node.name, self.uri, value, ts_float, tags)
        self.isac_node.pub_sub.publish(self.uri, (value, ts_float, tags))

    def survey_metadata(self):
        self._set_metadata(*self.isac_node.survey_value_metadata(self.uri))

    def get_history(self, time_period):
        t1, t2 = time_period
        if isinstance(t1, datetime):
            t1 = time.mktime(t1.timetuple()) + (t1.microsecond * 1e-6)
        if isinstance(t2, datetime):
            t2 = time.mktime(t2.timetuple()) + (t2.microsecond * 1e-6)

        peer_name = self.isac_node.survey_value_history(self.uri, (t1, t2))
        if not peer_name:
            raise NoPeerWithHistoryException('Could not find any peer that could provide history for %s' % self.uri)

        func_name = '.'.join((self.uri, 'get_history_impl'))
        data = self.isac_node.rpc.call_on(peer_name, func_name, (t1, t2))
        return [(point[0], datetime.fromtimestamp(point[1]), point[2]) for point in data]

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
