import json
import logging
import time
from .tools import green, Observable

from datetime import datetime

logger = logging.getLogger(__name__)

class IsacValue(object):

    def __init__(self, isac_node, name, initial_value=None, metadata=None, observers=Observable()):
        ts = datetime.now()

        self.isac_node = isac_node
        self.name = name
        self._metadata = metadata
        self.observers = observers
        self.metadata_observers = Observable()

        self.isac_node.rpc_service.register(
            lambda: (self._value, self.timestamp_float),
            name=self.name
        )

        self._value = initial_value
        if initial_value is None:
            self._value, self._timestamp = None, datetime.fromtimestamp(0)
            self.update_value_from_isac(*self.isac_node.survey_last_value(self.name, limit_peers=1))
        elif isinstance(initial_value, tuple):
            last_value, last_ts = self.isac_node.survey_last_value(self.name, limit_peers=1)
            if initial_value[1] > last_ts: # We want to publish our last value to anyone outside
                print 'publishing former value', initial_value
                self.value_ts = initial_value
            else: # We want to notify all our internal subscribers of the newer last value
                self._value, self._timestamp = None, datetime.fromtimestamp(0)
                self.update_value_from_isac(last_value, last_ts)
        else:
            print 'publishing value', initial_value
            self.value_ts = initial_value, ts

        #print '>>>>>', self.name, id(self), type(self._metadata), self._metadata
        if self._metadata:
            self.isac_node.event_value_metadata_update(self.name, self._metadata)

        self.isac_node.subscribe(name, self)

        self.isac_node.event_isac_value_entering(self.name)

    def __del__(self):
        if self.name in self.isac_node.rpc_service.procedures:
            del self.isac_node.rpc_service.procedures[self.name]

    #def register(self, observer):
    #    if observer not in self._observers:
    #        logger.debug('Registering %s on %s', observer.__name__, self.name)
    #        self._observers.append(observer)

    #def unregister(self, observer):
    #    if observer in self._observers:
    #        logger.debug('Unregistering %s from %s', observer.__name__, self.name)
    #        self._observers.remove(observer)

    #def _fire(self, *args, **kwargs):
    #    for observer in self._observers:
    #        green.spawn(observer, *args, **kwargs)

    @property
    def value(self, refresh=True):
        if refresh:
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
        self.isac_node.event_value_metadata_update(self.name, self._metadata)

    def _set_metadata(self, metadata):
        self._metadata = metadata
        if self._metadata:
            self.metadata_observers(self.name, self._metadata)

    def update_value_from_isac(self, new_value, ts_float):
        if ts_float > self.timestamp_float:
            self._value = new_value
            self._timestamp = datetime.fromtimestamp(ts_float)
            self.observers(self.name, self._value, self._timestamp)
        elif ts_float < self.timestamp_float:
            logger.warning('Trying to update value %s with a value older than what we have (%f vs. %f)', self.name, ts_float, self.timestamp_float)
        # else equal time => do nothing

    def publish_value(self, value, ts):
        ts_float = self.timestamp_float
        logger.info('Publishing for %s: %s, %s', self.name, value, ts_float)
        self.isac_node.pub.send_multipart([
            self.name,
            json.dumps((value, ts_float))
        ])

    def survey_metadata(self):
        self._set_metadata(self.isac_node.survey_value_metadata(self.name))

    def get_history(self, time_period):
        peer_name = self.isac_node.survey_value_history(self.name, time_period)
        if not peer_name:
            raise Exception('Could not find any peer that could provide history for %s' % self.name)

        t1, t2 = time_period
        if isinstance(t1, datetime):
            t1 = time.mktime(t1.timetuple()) + (t1.microsecond * 1e-6)
        if isinstance(t2, datetime):
            t2 = time.mktime(t2.timetuple()) + (t2.microsecond * 1e-6)

        data = self.isac_node.rpc_clients[peer_name][1].call('.'.join((self.name, 'get_history_impl')), args=[(t1, t2)])
        return [(point[0], datetime.fromtimestamp(point[1])) for point in data]

    def __str__(self):
        return '{0}: {1}'.format(self.timestamp, self.value)
