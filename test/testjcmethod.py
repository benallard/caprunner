import unittest

from testconfig import *

from caprunner.resolver import linkResolver
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod

class TestJavaCardMethod(unittest.TestCase):
    
    def testInit(self):
        rslvr = linkResolver()
        jcmtd = JavaCardStaticMethod(175, javatest_cap, rslvr)
        jcmtd = JavaCardVirtualMethod(0, 8, javatest_cap, rslvr)
        self.assertEquals(2, len(jcmtd.excpt_handlers))
