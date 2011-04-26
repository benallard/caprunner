import unittest

from testconfig import *

from methods import JavaCardStaticMethod

class TestJavaCardMethod(unittest.TestCase):
    
    def testInit(self):
        jcmtd = JavaCardStaticMethod(155, javatest_cap)

