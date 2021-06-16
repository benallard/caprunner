import unittest

from testconfig import *

from caprunner.resolver import linkResolver
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod

class TestJavaCardMethod(unittest.TestCase):
    
    def testInit(self):
        rslvr = linkResolver()
        jcmtd = JavaCardStaticMethod(109, javatest_cap, rslvr)
        jcmtd = JavaCardVirtualMethod(0, 8, False, javatest_cap, rslvr)
        self.assertEqual(2, len(jcmtd.excpt_handlers))
