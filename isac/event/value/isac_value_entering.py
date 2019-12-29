# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import logging

# Third-party imports

# Local imports
from isac.tools import Observable
from .. import Event

logger = logging.getLogger(__name__)


class IsacValueEnteringEvent(Event):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self._obs = Observable()

    def send(self, value_uri):
        logger.info(
            '(%s) Sending event for an entering isac value for %s', self.isac_node.name, value_uri)
        data = {
            'event_name': self.name(),
            'data': value_uri
        }
        self.transport.send_event(data)

    def process_event(self, peer_name, value_uri):
        logger.info(
            '(%s) EVENT isac value entering from %s: %s', self.isac_node.name, peer_name, value_uri)
        self._obs(peer_name.decode(), value_uri)

    def register_observer(self, observer):
        if not self._obs:
            self.transport.join_event()

        logger.debug('(%s) Registering %s', self.isac_node.name, observer.__name__)
        self._obs += observer

    def unregister_observer(self, observer):
        logger.debug('(%s) Unregistering %s', self.isac_node.name, observer.__name__)
        self._obs -= observer

        if not self._obs:
            self.transport.leave_event()
