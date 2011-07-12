import unittest

import python
from caprunner.interpreter import JavaCardVM

class TestOpcodes(unittest.TestCase):

    def _teststack(self, opcode, params, init, expected):
        vm = JavaCardVM(None)
        vm.frame.stack = init
        f = getattr(vm, opcode)
        f(*params)
        self.assertEquals(expected, vm.frame.stack)

    def _testBranch(self, opcode, params, stack, expectedIP):
        vm = JavaCardVM(None)
        vm.frame.stack = stack
        f = getattr(vm, opcode)
        offset = f(*params)
        if offset is None:
            offset = 0
        self.assertEquals(expectedIP, offset)
        

    def test_swap_x(self):
        self._teststack('swap_x', [0x11], [0,1,2,3,4,5,6,7,8], [0,1,2,3,4,5,6,8,7])
        self._teststack('swap_x', [0x43], [0,1,2,3,4,5,6,7,8], [0,1,5,6,7,8,2,3,4])
        self._teststack('swap_x', [0x13], [0,1,2,3,4,5,6,7,8], [0,1,2,3,4,8,5,6,7])

    def test_dup(self):
        self._teststack('dup', [], [0,1,2], [0,1,2,2])

    def test_dup2(self):
        self._teststack('dup2', [], [2,3,4], [2,3,4,3,4])

    def test_dup_x(self):
        self._teststack('dup_x', [0x12], [0,1,2,3,4,5,6,7,8], [0,1,2,3,4,5,6,8,7,8])
        self._teststack('dup_x', [0x48], [0,1,2,3,4,5,6,7,8], [0,5,6,7,8,1,2,3,4,5,6,7,8])
        self._teststack('dup_x', [0x30], [0,1,2,3,4,5,6,7,8], [0,1,2,3,4,5,6,7,8,6,7,8])

    def test_arraylength(self):
        self._teststack('arraylength', [], [[1,2,3,4,5,6,7,8]], [8])
        self._teststack('arraylength', [], [[i for i in xrange(765)]], [765])

    def test_s2b(self):
        bytes = xrange(-128, 127)
        for i in bytes:
            self._teststack('s2b', [], [i], [i])

        outbytes = [(0xffff,-1), (0x100,0), (0xfff,-1)]
        for i,j in outbytes:
            self._teststack('s2b', [], [i], [j])

    def test_baload(self):
        array = [i for i in xrange(10)]
        self._teststack('baload', [], [array, 6], [6])
        try:
            self._teststack('baload', [], [array, 12], [6])
            self.fail()
        except python.lang.ArrayIndexOutOfBoundsException:
            pass
        try:
            self._teststack('baload', [], [array, -2], [6])
            self.fail()
        except python.lang.ArrayIndexOutOfBoundsException:
            pass
        try:
            self._teststack('baload', [], [None,6], [6])
            self.fail()
        except python.lang.NullPointerException:
            pass

    def test_ifnonnull_w(self):
        self._testBranch('ifnonnull_w', [0x5], [None], 0)
        self._testBranch('ifnonnull_w', [0x5], [self], 5)
        self._testBranch('ifnonnull_w', [0xffff], [self], -1)
