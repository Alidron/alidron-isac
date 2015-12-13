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
from random import randint

logger = logging.getLogger(__name__)

_BUILTIN_SURVEYS = [
    '.value',
]

class Survey(object):

    def __init__(self, isac_node, transport):
        self.isac_node = isac_node
        self.transport = transport

        self.timeout = 0.5
        self.limit_peers = 0

    @classmethod
    def name(cls):
        return cls.__name__

    def _consume_arg(self, arg_name, default_value, kwargs):
        if arg_name in kwargs:
            value = kwargs[arg_name]
            del kwargs[arg_name]
            return value
        else:
            return default_value

    def ask(self, *args, **kwargs):
        timeout = self._consume_arg('timeout', self.timeout, kwargs)
        limit_peers = self._consume_arg('limit_peers', self.limit_peers, kwargs)

        request = {
            'req_id': ('%x' % randint(0, 0xFFFFFFFF)).encode(),
            'function': self.name(),
            'args': args,
            'kwargs': kwargs
        }

        results = self.transport.send_survey(request, timeout, limit_peers)

        return self.process_result(results)

    def reply(self, peer_id, request_id, data):
        reply = {
            'req_id': request_id,
            'data': data
        }
        self.transport.reply_survey(peer_id, reply)

    def process_request(self, peer_id, request_id, *args):
        pass

    def process_result(self, results):
        return results

class SurveysManager(object):

    def __init__(self, isac_node, transport):
        self.isac_node = isac_node
        self.transport = transport

        self.loaded_surveys = {}
        for builtin_survey in _BUILTIN_SURVEYS:
            survey_package = importlib.import_module(builtin_survey, __package__)
            for survey_name in survey_package.__all__:
                self.load(getattr(survey_package, survey_name))

    def load(self, survey_class):
        class_name = survey_class.name()
        self.loaded_surveys[class_name] = survey_class(self.isac_node, self.transport)

    def call(self, name, *args, **kwargs):
        return self.loaded_surveys[name].ask(*args, **kwargs)

    def on_survey(self, peer_id, peer_name, request):
        if request['function'] in self.loaded_surveys:
            self.loaded_surveys[request['function']].process_request(peer_id, request['req_id'], *request['args'], **request['kwargs'])
        else:
            logger.warning('(%s) Rejecting request to unknown survey: %s', self.isac_node.name, request['function'])
