import unittest

from resolver import linkResolver
from exportfile import ExportFile

class TestResolver(unittest.TestCase):
    
    def test_basicPackage(self):
        rslvr = linkResolver()
        self.assertTrue(rslvr.hasPackage('\xa0\x00\x00\x00b\x00\x01'))
        self.assertFalse(rslvr.hasPackage('\xa0'))

    def test_resolveStaticMethod(self):
        rslvr = linkResolver()
        self.assertEqual("", rslvr.resolveStaticMethod('\xa0\x00\x00\x00b\x01\x01', 3, 0))

    def test_addExportFile(self):
        rslvr = linkResolver()
        self.assertFalse(rslvr.hasPackage('\xA0\x00\x00\x00\x18\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01'))
        rslvr.addExportFile(ExportFile(open('../javatest/javacard/javatest.exp').read()))
        self.assertTrue(rslvr.hasPackage('\xA0\x00\x00\x00\x18\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01'))
