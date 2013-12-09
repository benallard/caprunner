#!python

import sys

from caprunner.exportfile import ExportFile

f = open(sys.argv[1], 'rb')
exp = ExportFile(f.read())
exp.pprint()
