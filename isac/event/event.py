# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import importlib
import logging

# Third-party imports

# Local imports

logger = logging.getLogger(__name__)

_BUILTIN_EVENTS = [
    '.value',
]


class Event(object):

    def __init__(self, isac_node, transport):
        self.isac_node = isac_node
        self.transport = transport

    @classmethod
    def name(cls):
        return cls.__name__

    def process_event(self, *args):
        pass


class EventsManager(object):

    def __init__(self, isac_node, transport):
        self.isac_node = isac_node
        self.transport = transport

        self.loaded_events = {}
        for builtin_event in _BUILTIN_EVENTS:
            event_package = importlib.import_module(builtin_event, __package__)
            for event_name in event_package.__all__:
                self.load(getattr(event_package, event_name))

    def load(self, event_class):
        class_name = event_class.name()
        self.loaded_events[class_name] = event_class(self.isac_node, self.transport)

    def send(self, name, *args, **kwargs):
        return self.loaded_events[name].send(*args, **kwargs)

    def call(self, name, attr, *args, **kwargs):
        return getattr(self.loaded_events[name], attr)(*args, **kwargs)

    def on_event(self, peer_id, peer_name, request):
        if request['event_name'] in self.loaded_events:
            self.loaded_events[request['event_name']].process_event(peer_name, request['data'])
