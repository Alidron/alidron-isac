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

from .. import Event
from ...tools import Observable

logger = logging.getLogger(__name__)

class IsacValueEnteringEvent(Event):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self._obs = Observable()

    def send(self, value_name):
        logger.info('Sending event for an entering isac value for %s', value_name)
        data = {
            'event_name': self.name(),
            'data': value_name
        }
        self.transport.send_event(data)

    def process_event(self, peer_name, value_name):
        logger.info('EVENT isac value entering from %s: %s', peer_name, value_name)
        self._obs(peer_name, value_name)

    def register_observer(self, observer):
        if not self._obs:
            self.transport.join_event()

        logger.debug('Registering %s', observer.__name__)
        self._obs += observer

    def unregister_observer(self, observer):
        logger.debug('Unregistering %s', observer.__name__)
        self._obs -= observer

        if not self._obs:
            self.transport.leave_event()
