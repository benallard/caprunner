import python.lang

import bytecode, utils

from methods import PythonStaticMethod, JavaCardStaticMethod, PythonVirtualMethod

class JavaCardStack(list):
    """
    This is the operand stack
    it contains words (short)
    """
    def push_int(self, integer):
        self.push(integer & 0xffff)
        self.push((integer & 0xffff0000) >> 16)

    def pop_int(self):
        return self.pop() | (self.pop() << 16)
    
    # We are a stack after all ...
    push = list.append

class JavaCardLocals(dict):
    """
    The method parameters are the first local variables.
    0 being "self" in the majority of the cases
    Theorically, the number and type of the params is known ...
    The mapping is: index -> value
    """
    def __init__(self, *params):
        for i in xrange(len(params)):
            self[i] = params[i]

    def aget(self, index):
        """ Get an address """
        return self.get(index, None)

    def sget(self, index):
        """ Get a short """
        return self.get(index, 0)

    def asArray(self):
        """ Return the locals as an array. Good for calling functions """
        res = []
        keys = self.keys()
        keys.sort()
        for key in keys:
            res.append(self[key])
        return res

class JavaCardFrame(object):
    """
    A frame has its own local variables, stack, bytecodes
    A frame has its own Exception handlers
    A frame should also have its own context for security purposes.
    We will forget that for the moment
    """
    def __init__(self, params, bytecodes):
        self.bytecodes = bytecodes
        self.stack = JavaCardStack()
        self.locals = JavaCardLocals(*params)
        # Current instruction pointer
        self.ip = 0

    def push(self, val):
        self.stack.push(val)

    def pop(self):
        return self.stack.pop()

    def aget(self, index):
        return self.locals.aget(index)

    def sget(self, index):
        return self.locals.sget(index)

    def __str__(self):
        return "<JavaCardFrame: ip: %d, locals: %s, bytecodes: %s>" % (
            self.ip,
            self.locals.asArray(),
            self.bytecodes)

class ExecutionDone(Exception):
    pass

class DummyFrame(object):
    """ 
    The bottom of the frame stack. 
    Only used to get the return value.
    """
    ip = -1
    def __init__(self):
        self.returnVal = None
    def push(self, val):
        self.returnVal = val
    def getValue(self):
        return self.returnVal

class JavaCardFrames(list):
    """
    This is the frame stack
    """
    def __init__(self):
        self.push(DummyFrame())

    def push(self, frame):
        self.append(frame)
        self.current = frame

    def pop(self):
        """ When we pop a frame, we don't care about the old one """
        list.pop(self)
        self.current = self[-1]

class JavaCardVM(object):
    def __init__(self, resolver):
        self.resolver = resolver
        # Stack of frames
        self.frames = JavaCardFrames()
        self.cap_file = None

    def load(self, cap_file):
        """
        Actually, this should create a `Context` for the given cap_file. Such
        that multiple context could coexist.
        """
        assert self.cap_file == None, "Cannot load two CAPFiles"
        self.cap_file = cap_file

    @property
    def frame(self):
        """ current frame """
        return self.frames.current

    def step(self):
        code = self.frame.bytecodes[self.frame.ip:]
        # get the function
        print self.frame
        f = getattr(self, bytecode.opname[code[0]])
        #print bytecode.opname[code[0]]
        #print len(self.frames)
        print self.frame.stack
        # get the params
        size, params = bytecode.getParams(code)
        # execute the function
        oldframe = self.frame
        inc = f(*params)
        # if we are done
        if isinstance(self.frame, DummyFrame):
            raise ExecutionDone
        # increment IP
        if inc is None:
            # regular function without branching
            inc = size
        oldframe.ip += inc

    def getRetValue(self):
        """ return the result of the finished execution """
        return self.frame.getValue()

# --- I'd like to split the opcodes interpretation from the rest

    def _invokestaticjava(self, method):
        """
        The resolver only gave us an empty JavaCardMethod. we first need
        to fill it with informations from the rest of te CAPFile, then push
        a new frame on top of the frame stack and we're done
        """
        # ouch, what happend to the int parameters ?
        params = self._popparams(method.nargs)
        self.frames.push(JavaCardFrame(params.asArray(), method.methodinfo.bytecodes))

    def _popparams(self, paramslen):
        """
        Local variables of type int are represented in two 16-bit cells, while 
        all others are represented in one 16-bit cell. If an entry in the local 
        variables array of the stack frame is reused to store more than one 
        local variable (for example, local variables from separate scopes), the 
        number of cells required for storage is two if one or more of the local 
        variables is of type int.
        """
        return JavaCardLocals(*reversed([self.frame.pop() for i in xrange(paramslen)]))

    def _pushretval(self, value, rettype):
        if rettype == 'integer':
            self.frame.push_int(val)
        elif rettype != 'void':
            self.frame.push(val)

    def _invokestaticnative(self, method):
        """ method is of type PythonMethod """
        # pop the params
        params = self._popparams(len(method.params))
        # call the method
        ret = method(*params.asArray())
        # push the returnvalue
        self._pushretval(ret, method.retType)

    def aload_0(self):
        self.aload(0)
    def aload_1(self):
        self.aload(1)
    def aload_2(self):
        self.aload(2)
    def aload_3(self):
        self.aload(3)
    def aload(self, index):
        self.frame.push(self.frame.aget(index))

    def sload_0(self):
        self.sload(0)
    def sload_1(self):
        self.sload(1)
    def sload_2(self):
        self.sload(2)
    def sload_3(self):
        self.sload(3)
    def sload(self, index):
        self.frame.push(self.frame.sget(index))

    def sconst_m1(self):
        self._sconst(-1)
    def sconst_0(self):
        self._sconst(0)
    def sconst_1(self):
        self._sconst(1)
    def sconst_2(self):
        self._sconst(2)
    def sconst_3(self):
        self._sconst(3)
    def sconst_4(self):
        self._sconst(4)
    def sconst_5(self):
        self._sconst(5)
    def _sconst(self, value):
        """ Not to be externaly called """
        self.frame.push(value)

    def srem(self):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        if val2 == 0:
            raise python.lang.ArithmeticException()
        self.frame.push(val1 - (val1 / val2) * val2)

    def sadd(self):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        self.frame.push(val1 + val2)

    def bspush(self, byte):
        self.frame.push(byte)

    def s2b(self):
        val = self.frame.pop()
        self.frame.push(val & 0xff)

    def sreturn(self):
        val = self.frame.pop()
        self.frames.pop()
        self.frame.push(val)

    def smul(self):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        self.frame.push((val1 * val2) & 0xffff)
        
    def ifne(self, branch):
        val = self.frame.pop()
        if val != 0:
            return utils.signed1(branch)

    def if_scmpge(self, branch):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        if val1 >= val2:
            return utils.signed1(branch)

    def goto(self, branch):
        return utils.signed1(branch)

    def sstore_0(self):
        self.sstore(0)
    def sstore_1(self):
        self.sstore(1)
    def sstore_2(self):
        self.sstore(2)
    def sstore_3(self):
        self.sstore(3)
    def sstore(self, index):
        val = self.frame.pop()
        self.frame.locals[index] = val

    def sspush(self, short):
        self.frame.push(short)

    def invokestatic(self, index):
        method = self.resolver.resolveIndex(index, self.cap_file)
        if isinstance(method, PythonStaticMethod):
            self._invokestaticnative(method)
        elif isinstance(method, JavaCardStaticMethod):
            self._invokestaticjava(method)

    def nop(self):
        pass

    def new(self, index):
        cls = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(object.__new__(cls.cls))

    def dup(self):
        self.frame.push(self.frame.stack[-1])

    def _invokespecialnative(self, method):
        """ looks like we have to add one paraneter to the list here ... """        
        params = self._popparams(len(method.params) + 1)
        # call the method
        ret = method(*params.asArray())
        # push the returnvalue
        self._pushretval(ret, method.retType)

    _invokespecialjava = _invokestaticjava

    def invokespecial(self, index):
        method = self.resolver.resolveIndex(index, self.cap_file)
        print method
        if isinstance(method, PythonStaticMethod):
            self._invokespecialnative(method)
        elif isinstance(method, JavaCardStaticMethod):
            self._invokespecialjava(method)

    def _invokevirtualnative(self, method):
        params = self._popparams(len(method.params))
        objref = self.frame.pop()
        method.bindToObject(objref)
        ret = method(*params.asArray())
        self._pushretval(ret, method.retType)

    def _invokevirtualjava(self, method):
        # we need to know how many parameters we need to pop before getting objref
        params = self._popparams(method.nargs)
        #objref = params.aget(0)
        #mtd = objref.methods[method.token]
        self.frames.push(JavaCardFrame(params.asArray(), method.method_info.bytecodes))

    def invokevirtual(self, index):
        method = self.resolver.resolveIndex(index, self.cap_file)
        if isinstance(method, PythonVirtualMethod):
            self._invokevirtualnative(method)
        else:
            self._invokevirtualjava(method)

    def putfield_s(self, index):
        value = self.frame.pop()
        objref = self.frame.pop()
        token = self.resolver.resolveIndex(index, self.cap_file)
        objref.setFieldAt(token, value)

    def getfield_s_this(self, index):
        objref = self.frame.aget(0)
        token = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(token))

    def returnn(self):
        self.frames.pop()

    def pop(self):
        self.frame.pop()
