# Copyright (c) 2015-2020 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import logging  # noqa: F401
import re

# Third-party imports
import pytest

# Local imports
from isac.transport import PyreNode
from isac.tools import green

# logging.basicConfig(level=logging.DEBUG)


class StoreResults(object):
    def __init__(self):
        self.on_new_peer_results = None
        self.on_peer_gone_results = None
        self.on_survey_results = None
        self.on_event_results = None

    def on_new_peer(self, *args):
        self.on_new_peer_results = args

    def on_peer_gone(self, *args):
        self.on_peer_gone_results = args

    def on_survey(self, *args):
        self.on_survey_results = args

    def on_event(self, *args):
        self.on_event_results = args


@pytest.fixture(scope='function')
def node_with_callbacks(request):
    n = PyreNode('testA')

    results = StoreResults()
    n.on_new_peer = results.on_new_peer
    n.on_peer_gone = results.on_peer_gone
    n.on_survey = results.on_survey
    n.on_event = results.on_event

    yield n, results

    n.shutdown()
    green.sleep(0.1)  # Good to wait all other nodes shutdown


def wait_cb(results, cb_name, timeout=10, step=0.1):
    for i in range(int(timeout/step)):
        green.sleep(step)
        if getattr(results, cb_name + '_results'):
            break
    assert getattr(results, cb_name + '_results'), 'Callback %s not called' % cb_name


def test_on_new_peer(node_with_callbacks, request):
    nA, results = node_with_callbacks
    nA.run()

    nB = PyreNode('testB')
    request.addfinalizer(nB.shutdown)

    nB.set_header('rpc_proto', 'tcp')
    nB.set_header('rpc_port', str(999))
    nB.set_header('pub_proto', 'tcp')
    nB.set_header('pub_port', str(999))
    nB.run()

    wait_cb(results, 'on_new_peer')

    peer_id, peer_name, pub_endpoint, rpc_endpoint = results.on_new_peer_results
    assert peer_id == nB.uuid()
    assert peer_name == b'testB'
    assert re.match('^tcp://(.*):999$', pub_endpoint), 'Bad PUB endpoint'
    assert re.match('^tcp://(.*):999$', rpc_endpoint), 'Bad RPC endpoint'


def test_on_peer_gone(node_with_callbacks):
    nA, results = node_with_callbacks
    nA.run()

    nB = PyreNode('testB')
    nB_uuid = nB.uuid()
    try:
        nB.run()
        wait_cb(results, 'on_new_peer')
    finally:
        nB.shutdown()

    wait_cb(results, 'on_peer_gone')

    peer_id, peer_name = results.on_peer_gone_results
    assert peer_id == nB_uuid
    assert peer_name == b'testB'


def test_on_survey(node_with_callbacks, request):
    nA, results = node_with_callbacks
    nA.run()

    nB = PyreNode('testB')
    request.addfinalizer(nB.shutdown)

    nB.run()
    wait_cb(results, 'on_new_peer')

    nB.send_survey({'req_id': 'this is a test'}, 0.1, 1)

    wait_cb(results, 'on_survey')

    peer_id, peer_name, request = results.on_survey_results
    assert peer_id == nB.uuid()
    assert peer_name == b'testB'
    assert request == {'req_id': 'this is a test'}


def test_on_event(node_with_callbacks, request):
    nA, results = node_with_callbacks
    nA.run()
    nA.join('EVENT')

    nB = PyreNode('testB')
    request.addfinalizer(nB.shutdown)

    nB.run()
    wait_cb(results, 'on_new_peer')

    nB.send_event('various data')

    wait_cb(results, 'on_event')

    peer_id, peer_name, request = results.on_event_results
    assert peer_id == nB.uuid()
    assert peer_name == b'testB'
    assert request == 'various data'


def test_survey_process(node_with_callbacks, request):
    nA, results = node_with_callbacks
    nA.run()

    nB = PyreNode('testB')
    request.addfinalizer(nB.shutdown)

    nB.run()
    wait_cb(results, 'on_new_peer')

    # Test it can cope with wrong req_id
    nA.reply_survey(nB.uuid(), {'req_id': 'wrong!', 'data': ''})

    def _reply():
        wait_cb(results, 'on_survey')
        peer_id, peer_name, request = results.on_survey_results
        nA.reply_survey(peer_id, {'req_id': 'this is a test', 'data': 'OK!'})
    green.spawn(_reply)

    assert nB.send_survey({'req_id': 'this is a test'}, 1, 1) == [(b'testA', 'OK!')]
