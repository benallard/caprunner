import unittest

from testconfig import *

from caprunner.resolver import linkResolver
from caprunner.interpreter import JavaCardVM, JavaCardFrame, JavaCardLocals, JavaCardStack, DummyFrame

from pythoncard.framework import ISOException, Applet

class TestDummyFrame(JavaCardFrame, DummyFrame):
    def __init__(self, params):
        JavaCardFrame.__init__(self, params, [], 0)
    push = JavaCardFrame.push
    pop = JavaCardFrame.pop

class TestInterpreter(unittest.TestCase):

    def _run(self, intr):
        while intr.step():
            pass

    def testEasy(self):
        intr = JavaCardVM(None)
        intr.frames.push(TestDummyFrame([None, 4]))
        intr.sload_1()
        intr.bspush(58)
        intr.sadd()
        intr.s2b()
        intr.sreturn()
        self.assertEqual(62, intr.getRetValue())

    def testSomeIf(self):
        intr = JavaCardVM(None)
        intr.frames.push(JavaCardFrame([None, 6], [29, 5, 73, 97, 6, 29, 6, 69, 120, 3, 49, 30, 29, 109, 13, 30, 8, 65, 48, 30, 4, 65, 91, 49, 112, 243, 29, 120], 0))
        self._run(intr)

    def test_gcdRecursif(self):
        intr = JavaCardVM(linkResolver())
        intr.load(javatest_cap)
        intr.frames.push(JavaCardFrame([42,56], [29, 97, 4, 28, 120, 29, 28, 29, 73, 141, 0, 9, 120], 0))
        self._run(intr)
        self.assertEqual(14, intr.getRetValue())
        

    def test_gcdIteratif(self):
        intr = JavaCardVM(None)
        intr.frames.push(JavaCardFrame([42,56], [29, 97, 4, 28, 120, 28, 29, 73, 49, 29, 47, 30, 48, 112, 243], 0))
        self._run(intr)
        self.assertEqual(14, intr.getRetValue())

    def test_callExtStaticMethod(self):
        intr = JavaCardVM(linkResolver())
        intr.load(javatest_cap)
        intr.frames.push(JavaCardFrame([None, None], [17, 106, 129, 141, 0, 5, 122], 0))
        try:
            self._run(intr)
            self.fail()
        except ISOException as ioe:
            self.assertEqual(0x6A81, ioe.getReason())

    def test_objectCreation(self):
        intr = JavaCardVM(linkResolver())
        intr.load(javatest_cap)
        intr.frames.push(TestDummyFrame([None]))
        intr.new(2)
        intr.dup()
        intr.invokespecial(3)
        self._run(intr) # dig into
        intr.invokevirtual(4)
        intr.returnn()

    def test_callVirtualMethod(self):
        intr = JavaCardVM(linkResolver())
        intr.load(javatest_cap)
        intr.frames.push(TestDummyFrame([None]))
        intr.new(2)
        intr.dup()
        intr.invokespecial(3)
        self._run(intr)
        self.assertTrue(isinstance(intr.frame.stack[-1], Applet))
        for i in xrange(1,4):
            intr.dup()
            intr.sspush(i)
            intr.invokevirtual(7)
            self._run(intr)
            self.assertEqual(i, intr.frame.stack[-1])
            intr.pop()
        intr.returnn()

class TestLocals(unittest.TestCase):
    def test_init(self):
        loc = JavaCardLocals(4,5,6,7,8)
        self.assertEqual(4, loc[0])
        self.assertEqual(5, len(loc))

        array = [1,2,3,4]
        loc = JavaCardLocals(*array)
        self.assertEqual(3, loc[2])
        self.assertEqual(4, len(loc))

    def test_getparams(self):
        loc = JavaCardLocals(self,2)
        self.assertTrue(loc.aget(0) is self)
        self.assertEqual(2, loc.sget(1))

    def test_getlocals(self):
        loc = JavaCardLocals(self)
        self.assertEqual(0, loc.sget(3))
        self.assertTrue(loc.aget(1) is None)

    def test_asArray(self):
        array = [89,3,None,7]
        loc = JavaCardLocals(*array)
        self.assertEqual(array, loc.asArray())

class TestStack(unittest.TestCase):
    def test(self):
        s = JavaCardStack()
        s.push(2)
        self.assertEqual(2, s.pop())
        
