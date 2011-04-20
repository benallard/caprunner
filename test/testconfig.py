from exportfile import ExportFile
from capfile import CAPFile

javatest_exp = ExportFile(open('../javatest/javacard/javatest.exp').read())
javatest_cap = CAPFile('../javatest/javacard/javatest.cap')
