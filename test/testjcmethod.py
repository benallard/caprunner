import unittest

from testconfig import *

from jcmethod import JavaCardMethod

class TestJavaCardMethod(unittest.TestCase):
    
    def testInit(self):
        jcmtd = JavaCardMethod(javatest_cap, 151)
        
