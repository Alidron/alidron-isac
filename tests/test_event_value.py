import logging
import pytest

from isac import IsacNode, IsacValue
from isac.tools import green

# logging.basicConfig(level=logging.DEBUG)

@pytest.fixture(scope='module')
def two_nodes(request):
    nA = IsacNode('testA')
    nB = IsacNode('testB')

    def teardown():
        nA.shutdown()
        nB.shutdown()

    request.addfinalizer(teardown)
    return nA, nB

class Observer(object):

    def __init__(self):
        self.args = None

    def callback(self, *args):
        self.args = args

def test_isac_value_entering_event(two_nodes):
    nA, nB = two_nodes
    obs = Observer()

    nB.register_isac_value_entering(obs.callback)
    nA.event_isac_value_entering('test')

    green.sleep(0.25)

    assert obs.args, 'Callback not called'
    assert obs.args == ('testA', 'test')

    nB.unregister_isac_value_entering(obs.callback)
    nA.event_isac_value_entering('test2')

    green.sleep(0.25)

    assert obs.args == ('testA', 'test')

class FakeIsacValue(object):

    def __init__(self):
        self.metadata = None

    def _set_metadata(self, metadata):
        self.metadata = metadata

def test_value_metadata_update_event(two_nodes):
    nA, nB = two_nodes
    fake_iv = FakeIsacValue()
    nB.transport.join_event()

    green.sleep(0.25)

    nB.isac_values['test'] = fake_iv
    nA.event_value_metadata_update('test', {'this is': 'metadata'})

    green.sleep(0.25)

    assert fake_iv.metadata, 'Callback not called'
    assert fake_iv.metadata == {'this is': 'metadata'}
