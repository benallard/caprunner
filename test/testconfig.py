from caprunner.exportfile import ExportFile
from caprunner.capfile import CAPFile

import os

dir_path = os.path.dirname(os.path.realpath(__file__))

javatest_exp = ExportFile(open(os.path.join(dir_path, 'javatest/javacard/javatest.exp'), 'rb').read())
javatest_cap = CAPFile(os.path.join(dir_path,'javatest/javacard/javatest.cap'))
