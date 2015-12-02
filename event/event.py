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

import importlib
import logging

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
