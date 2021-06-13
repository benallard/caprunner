from caprunner.exportfile import ExportFile
from caprunner.capfile import CAPFile

javatest_exp = ExportFile(open('javatest/javacard/javatest.exp', 'rb').read())
javatest_cap = CAPFile('javatest/javacard/javatest.cap')
