import new, dis

def stack(offset):
    def neew(f):
        def new(self, *params):
            f(self, *params)
            self.current_stack_size += offset
            self.max_stack_size = max(self.max_stack_size, self.current_stack_size)
        return new
    return neew

def operation(name):
    def neew(f):
        def new(self, *params):
            self.bytecode.append(dis.opmap["LOAD_CONST"])
            self.current_position += 1
            f(self, *params)
        return new
    return neew

class Method(object):
    """
    This is a Python method, and has no notion of Java.
    """
    # Python code flags
    CO_OPTIMIZED              = 0x0001      # use LOAD/STORE_FAST instead of _NAME
    CO_NEWLOCALS              = 0x0002      # only cleared for module/exec code
    CO_VARARGS                = 0x0004
    CO_VARKEYWORDS            = 0x0008
    CO_NESTED                 = 0x0010      # ???
    CO_GENERATOR              = 0x0020
    CO_NOFREE                 = 0x0040      # set if no free or cell vars
    CO_GENERATOR_ALLOWED      = 0x1000      # unused
    def __init__(self, name, isStatic=False):
        self.name = name
        self.isStatic = isStatic
        self.bytecode = []
        self.max_stack_size = 0
        self.current_stack_size = 0
        self.current_position = 0
        self.nb_locals = 0
        self.names = []
        # value -> index
        self.constants = {}

    def appendshort(self, short):
        self.bytecode.append(short & 0xff)
        self.bytecode.append((short & 0xff00) >> 8)

    def updatelocals(self, index):
        self.nb_locals = max(self.nb_locals, index)

    @stack(1)
    @operation("LOAD_FAST")
    def load_fast(self, index):
        self.appendshort(index)
        self.updatelocals(index)

    @stack(1)
    @operation("LOAD_CONST")
    def load_const(self, value):
        if value not in self.constants:
            self.constants[value] = len(self.constants)
        self.appendshort(self.constants[value])

    @stack(-1)
    @operation("BINARY_MODULO")
    def binary_modulo(self): pass
        # I like that one ...

    @stack(-1)
    @operation("COMPARE_OP")
    def compare_op(self, op):
        self.appendshort(dis.cmp_op.index(op))

    @stack(-1)
    @operation("POP_TOP")
    def pop_top(self): pass

    def get(self):
        nargs = self.isStatic and 0 or 1 # self
        code = new.code(argcount = nargs,
                        nlocals = self.nb_locals,
                        stacksize = self.max_stack_size,
                        flags = self.CO_OPTIMIZED | self.CO_NEWLOCALS | self.CO_VARARGS | self.CO_NOFREE,
                        codestring = self.bytecode,
                        constants = self.constants,
                        names = self.names,
                        varnames = (),
                        name = self.name,
                        # Debug Component could be of help there
                        filename = "", firstlineno = 0, lnotab = "") 
        fn = new.function(code, global_names)
        if self.isStatic:
            fn = staticmethod(fn)
        return fn

class Translator(object):
    """ I hope to be able to reuse a lot from the BytecodeTranslator there """
    def __init__(self, method):
        self.method = method

    def sload_1(self):
        self.method.load_fast(1)

    def sconst_2(self):
        self.method.load_const(2)

    def srem(self):
        self.method.binary_modulo()

    def ifne(self, branch):
        self.method.load_const(0)
        self.method.compare_op('!=')
        self.method.jump_if_true(branch) # We need a pop_top at the other destination also ...
        self.method.pop_top()

if __name__ == "__main__":
    mtd = Method("testSomeIf")
    talk = Translator(mtd)
    talk.sload_1()
    talk.sconst_2()
    talk.srem()
    f = mtd.get()
    print(f(5))
"""
    talk.ifne(6)
    talk.sload_1()
    talk.sconst_3()
    talk.smul()
    talk.sreturn()
    talk.sconst_0()
    talk.sstore_2(),
    talk.sload_2()
    talk.sload_1()
    talk.ifscmpge(13)
    talk.sload_2()
    talk.sconst_5()
    talk.sadd()
    talk.sstore_1()
    talk.sload_2()
    talk.sconst_1()
    talk.sadd()
    talk.s2b()
    talk.sstore_2()
    talk.goto(243)
    talk.sload_1()
    talk.sreturn()
"""
