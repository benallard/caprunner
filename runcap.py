#!/usr/bin/env python

from caprunner import capfile
from caprunner.utils import a2s, signed1

from caprunner.jtoken import Token

def hexify(hexStr):
    """
    Turns a string of hexadecimal nibbles into an array of numbers
    >>> hexify("00200003083132333400000000")
    [0, 32, 0, 3, 8, 49, 50, 51, 52, 0, 0, 0, 0]
    """
    bytes = []
    hexStr = ''.join( hexStr.split() )
    for i in range(0, len(hexStr), 2):
        bytes.append( signed1( int (hexStr[i:i+2], 16 ) ) )
    return bytes

class Runner(Token):

    def checkreceive(self, expected, received):
        print(f"<== {a2s(received)}")
        if expected != received:
            print(f"<== {a2s(expected)} was expected")
            print(self.vm.log)
            sys.exit(1)

    def echo(self, *args, **kwargs):
        print(args, kwargs)

    def run(self):
        send = []
        receive = []
        for line in sys.stdin:
            line = line.rstrip()
            if '--' in line: # remove the comment
                line = line[:line.find('--')]
            if len(line) == 0 and len(send) != 0 and len(receive) != 0:
                print(f"==> {a2s(send)}")
                try:
                    got = self.transmit(send)
                except:
                    print(self.vm.log)
                    raise
                self.checkreceive(receive, got)
                send = []
                receive = []
            if line[:4] == "==> ":
                send.extend(hexify(line[4:]))
            elif line[:4] == "<== ":
                receive.extend(hexify(line[4:]))
            elif line.startswith('install:'):
                sep1 = 8
                sep2 = line.find(':', sep1+1)
                data = hexify(line[sep1:sep2])
                offset = hexify(line[sep2 + 1:])[0]
                self.install(data, offset)
            elif line.startswith('load:'):
                self.vm.load(capfile.CAPFile(line[5:].strip()))
            elif line.startswith('log;'):
                print(self.vm.log)
            else:
                print(line)

def main(args):
    if len(args) > 1:
        version = tuple([int(i) for i in args[1].split('.')])
        print("Running in version %s.%s.%s" % version)
        runner = Runner(version)
    else:
        runner = Runner()

    runner.run()

if __name__ == "__main__":
    import sys
    main(sys.argv)