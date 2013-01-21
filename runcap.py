#!/usr/bin/env python

import sys

from caprunner import capfile
from caprunner.utils import s2a, a2s

from caprunner.token import Token

class Runner(Token):

    def checkreceive(self, expected, received):
        print "<== %s" % a2s(received)
        if expected != received:
            print "<== %s was expected" % a2s(expected)
            print self.vm.log
            sys.exit(1)

    def echo(self, *args, **kwargs):
        print(args, kwargs)

    def run(self):
        send = []
        receive = []
        for line in sys.stdin:
            line = line.rstrip()
            if len(line) == 0 and len(send) != 0 and len(receive) != 0:
                print "==> %s" % a2s(send)
                try:
                    got = self.transmit(send)
                except:
                    print self.vm.log
                    raise
                self.checkreceive(receive, got)
                send = []
                receive = []
            if line[:4] == "==> ":
                send.extend(s2a(line[4:]))
            elif line[:4] == "<== ":
                receive.extend(s2a(line[4:]))
            elif line.startswith('install:'):
                sep1 = 8
                sep2 = line.find(':', sep1+1)
                data = s2a(line[sep1:sep2])
                offset = s2a(line[sep2 + 1:])[0]
                self.install(data, offset)
            elif line.startswith('load:'):
                self.vm.load(capfile.CAPFile(line[5:].strip()))
            elif line.startswith('log;'):
                print self.vm.log
            else:
                print line

if len(sys.argv) > 1:
    version = tuple([int(i) for i in sys.argv[1].split('.')])
    print "Running in version %s.%s.%s" % version
    runner = Runner(version)
else:
    runner = Runner()

runner.run()
