import sys
import unittest

from testconfig import *

from caprunner.resolver import linkResolver
from pythoncard.framework import ISOException, Applet

class TestResolver(unittest.TestCase):
    
    def test_basicPackage(self):
        rslvr = linkResolver()
        self.assertTrue(rslvr.hasPackage('\xa0\x00\x00\x00b\x00\x01'))
        self.assertFalse(rslvr.hasPackage('\xa0'))

    def test__resolveExtStaticMethod(self):
        rslvr = linkResolver()
        # ISOExcption.throwIt
        mtd = rslvr._resolveExtStaticMethod('\xa0\x00\x00\x00b\x01\x01', 7, 1)
        try:
            mtd(0x9000)
            self.fail()
        except ISOException as ioe:
            self.assertEqual(0x9000, ioe.getReason())

    def test_resolveIndex(self):
        rslvr = linkResolver()
        mtd = rslvr.resolveIndex(5, javatest_cap)
        try:
            mtd(0x9000)
            self.fail()
        except ISOException as ioe:
            self.assertEqual(0x9000, ioe.getReason())

        cls = rslvr.resolveIndex(2, javatest_cap)
        self.assertTrue(issubclass(cls.cls, Applet))

    def test__resolveExtClass(self):
        rslvr = linkResolver()
        self.assertEqual(ISOException, rslvr._resolveExtClass('\xa0\x00\x00\x00b\x01\x01', 7).cls)

    def test_addExportFile(self):
        rslvr = linkResolver()
        self.assertFalse(rslvr.hasPackage('\xA0\x00\x00\x00\x18\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01'))
        rslvr.addExportFile(javatest_exp)
        self.assertTrue(rslvr.hasPackage('\xA0\x00\x00\x00\x18\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01'))

    def test_getModule(self):
        rslvr = linkResolver()
        from python import lang as java_lang
        self.assertEqual(java_lang, rslvr._getModule('java.lang'))

