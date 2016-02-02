# Copyright (c) 2015-2016 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from isac import IsacNode, IsacValue

import cmd
import sys
import time
import traceback

import gevent as green
from gevent.fileobject import FileObject

from pprint import pprint as pp

class IsacCmd(cmd.Cmd):

    def __init__(self, isac_node, values):
        cmd.Cmd.__init__(self, stdin=FileObject(sys.stdin))
        self.use_rawinput = False
        self.isac_node = isac_node
        self.values = values

    def do_val1(self, args):
        print self.values['test://isac_cmd/this/is/a/test']

    def do_val2(self, args):
        print self.values['test://isac_cmd/this/is/another/test']

    def do_new(self, args):
        self.values[args] = IsacValue(self.isac_node, args)

    def do_set(self, args):
        args = args.split(' ')
        if args[0] not in self.values:
            self.do_new(args[0])
            
        self.values[args[0]].value = eval(args[1])

    def do_get(self, args):
        if args not in self.values:
            self.do_new(args)
            
        print self.values[args].value_ts_tags

    def do_p(self, args):
        green.sleep(0.1)

    def do_peers(self, args):
        pp(self.isac_node.transport.peers())

    def do_call(self, args):
        args = args.split(' ')
        print self.isac_node.call_rpc(*args)

    def do_test1(self, args):
        signals = sorted(self.isac_node.survey_value_uri(args))
        pp(signals)
        with open('/logs/signal_list.txt', 'w') as f:
            for signal in signals:
                f.write(signal + '\n')

    def do_test2(self, args):
        print self.isac_node.survey_last_value(args)

    def do_test3(self, args):
        print self.isac_node.survey_value_metadata(args)

    def do_test4(self, args):
        print self.isac_node.survey_values_metadata(args.split(' '), limit_peers=2)

    def do_test5(self, args):
        print self.isac_node.survey_values_metadata(args, is_re=True, limit_peers=2)

    def do_test6(self, args):
        self.values[args].survey_metadata()

    def do_test7(self, args):
        pp(self.isac_node.survey_values_metadata('ozw/.*', is_re=True, limit_peers=1))

    def do_history(self, args):
        pp(self.values[args].get_history((time.time()-86400, time.time())))

    def do_metadata(self, args):
        print self.values[args].metadata

    def do_shell(self, args):
        try:
            exec args
        except:
            print traceback.format_exc()

    def do_stop(self, args):
        self.isac_node.shutdown()

    def do_EOF(self, args):
        self.do_stop(None)
        return -1

    def postloop(self):
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

def ping(*args, **kwargs):
    return 'PONG!', args, kwargs


if __name__ == '__main__':
    isac_node = IsacNode(sys.argv[1])
    isac_node.add_rpc(ping)

    #val = IsacValue(isac_node, 'switch://dimer001/switch_binary/switch')
    #green.sleep(0.1)
    #val.value = not val.value
    #green.sleep(0.1)

    try:
        def notify_isac_value_entering(peer_name, value_name):
            print '>>>>', peer_name, value_name

        # if sys.argv[1] in ['test01', 'gdsjkl01']:
        isac_node.register_isac_value_entering(notify_isac_value_entering)


        if sys.argv[1] in ['test01', 'gdsjkl01']:
            val1 = IsacValue(isac_node, 'test://isac_cmd/this/is/a/test', 12, metadata={'is_read_only': False, 'genre': 'test'})
        # else:
        #     val1 = IsacValue(isac_node, 'this.is.a.test')

        if sys.argv[1] in ['test02', 'fdsfds02']:
            val2 = IsacValue(isac_node, 'test://isac_cmd/this/is/another/test', 42, metadata={'is_read_only': True, 'genre': 'real'})
        # else:
        #     val2 = IsacValue(isac_node, 'this.is.another.test')

        def notifyer(name, value, ts):
            print name, value, ts

        # val1.observers += notifyer
        # val2.observers += notifyer

        # isac_cmd = IsacCmd(isac_node, {'this.is.a.test': val1, 'this.is.another.test': val2})
        isac_cmd = IsacCmd(isac_node, {})
        isac_cmd.cmdloop()

    except:
        isac_node.shutdown()
        raise
