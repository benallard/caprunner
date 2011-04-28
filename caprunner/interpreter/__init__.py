import python.lang

from caprunner import bytecode, utils

from caprunner.interpreter.methods import PythonStaticMethod, JavaCardStaticMethod, PythonVirtualMethod

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
    def __init__(self, params, bytecodes, handlers = []):
        self.bytecodes = bytecodes
        self.handlers = handlers
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
    Actually, we need a stack to pass parameters ...
    """
    ip = -1
    def __init__(self):
        self.returnVal = None
        self.stack = []
    def push(self, val):
        self.stack.append(val)
    def pop(self):
        return self.stack.pop()
    def getValue(self):
        return self.stack[-1]

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
        assert self.cap_file is None, "Cannot load two CAPFiles, don't know about contexts yet"
        self.cap_file = cap_file

    @property
    def frame(self):
        """ current frame """
        return self.frames.current

    def step(self):
        code = self.frame.bytecodes[self.frame.ip:]
        # get the function
        f = getattr(self, bytecode.opname[code[0]])
        # get the params
        size, params = bytecode.getParams(code)
        # execute the function
        frame = self.frame
        inc = None
        print bytecode.opname[code[0]], params
        print frame.stack
        print frame.ip
        #print frame.locals
        try:
            inc = f(*params)
        except Exception, e:
            print "caught exception: ", type(e)
            while not isinstance(self.frame, DummyFrame):
                for handler in self.frame.handlers:
                    if self.frame.ip in handler:
                        if handler.match(e):
                            print "exception handled: ip = ", handler.handler_offs
                            self.frame.ip = handler.handler_offs
                            self.frame.push(e)
                            return
                        if handler.last:
                            break
                print "%d local handlers exhausted poping frame" % len(self.frame.handlers)
                self.frames.pop()
            # not handled, re-raise
            print "exception not handled, re-raising"
            raise
                    
        # if we are done
        if isinstance(self.frame, DummyFrame):
            raise ExecutionDone
        # increment IP
        if inc is None:
            # regular function without branching
            inc = size
        frame.ip += inc

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
        self.frames.push(JavaCardFrame(params.asArray(), method.bytecodes, method.excpt_handlers))

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
            self.frame.push_int(value)
        elif rettype != 'void':
            self.frame.push(value)

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
        self.frame.push(self.frame.locals[index])

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

    def baload(self):
        index = utils.signed2(self.frame.pop())
        arrayref = self.frame.pop()
        if arrayref is None:
            raise python.lang.NullPointerException()
        if index < 0:
            raise python.lang.ArrayIndexOutOfBoundsException()
        try:
            value = arrayref[index]
        except IndexError:
            raise python.lang.ArrayIndexOutOfBoundsException()
        self.frame.push(value)

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

    def aconst_null(self):
        self.frame.push(None)

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

    def ssub(self):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        self.frame.push(utils.signed2((val1 - val2) & 0xffff))

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

    def _ifxx(self, branch, op):
        val = self.frame.pop()
        if {'eq': val == 0,
            'ne': val != 0,
            'lt': val < 0,
            'le': val <= 0,
            'gt': val > 0,
            'ge': val >= 0}[op]:
            return utils.signed1(branch)
    def ifeq(self, branch):
        return self._ifxx(branch, 'eq')
    def ifne(self, branch):
        return self._ifxx(branch, 'ne')
    def iflt(self, branch):
        return self._ifxx(branch, 'lt')
    def ifle(self, branch):
        return self._ifxx(branch, 'le')
    def ifgt(self, branch):
        return self._ifxx(branch, 'gt')
    def ifge(self, branch):
        return self._ifxx(branch, 'ge')

    def _if_scmpxx(self, branch, op):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        if {'eq': val1 == val2,
            'ne': val1 != val2,
            'lt': val1 < val2,
            'le': val1 <= val2,
            'gt': val1 > val2,
            'ge': val1 >= val2}[op]:
            return utils.signed1(branch)

    def if_scmpeq(self, branch):
        return self._if_scmpxx(branch, 'eq')
    def if_scmpne(self, branch):
        return self._if_scmpxx(branch, 'ne')
    def if_scmplt(self, branch):
        return self._if_scmpxx(branch, 'lt')
    def if_scmple(self, branch):
        return self._if_scmpxx(branch, 'le')
    def if_scmpgt(self, branch):
        return self._if_scmpxx(branch, 'gt')
    def if_scmpge(self, branch):
        return self._if_scmpxx(branch, 'ge')

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

    def astore_0(self):
        self.astore(0)
    def astore_1(self):
        self.astore(1)
    def astore_2(self):
        self.astore(2)
    def astore_3(self):
        self.astore(3)
    def astore(self, index):
        objref = self.frame.pop()
        self.frame.locals[index] = objref

    def bastore(self):
        value = self.frame.pop()
        index = self.frame.pop()
        arrayref = self.frame.pop()
        arrayref[utils.signed2(index)] = value

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

    def newarray(self, elemtype):
        count = utils.signed2(self.frame.pop())
        if count < 0:
            raise python.lang.NegativeArraySizeException()
        array = [{10:False, 11:0, 12:0, 13:0}[elemtype] for i in xrange(count)]
        self.frame.push(array)

    def dup(self):
        value = self.frame.pop()
        self.frame.push(value)
        self.frame.push(value)

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
        self.frames.push(JavaCardFrame(params.asArray(), method.bytecodes, method.excpt_handlers))

    def invokevirtual(self, index):
        method = self.resolver.resolveIndex(index, self.cap_file)
        if isinstance(method, PythonVirtualMethod):
            self._invokevirtualnative(method)
        else:
            self._invokevirtualjava(method)

    def putfield_b(self, index):
        value = bool(self.frame.pop())
        objref = self.frame.pop()
        token = self.resolver.resolveIndex(index, self.cap_file)
        objref.setFieldAt(token, value)
    def putfield_s(self, index):
        value = self.frame.pop()
        objref = self.frame.pop()
        token = self.resolver.resolveIndex(index, self.cap_file)
        objref.setFieldAt(token, value)

    putfield_a = putfield_s
    putfield_b = putfield_s

    def getfield_b_this(self, index):
        objref = self.frame.aget(0)
        token = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(bool(objref.getFieldAt(token)))

    def getfield_s_this(self, index):
        objref = self.frame.aget(0)
        token = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(token) or 0)

    def getfield_a_this(self, index):
        objref = self.frame.aget(0)
        token = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(token) or None)

    def getfield_a(self, index):
        objref = self.frame.pop()
        token = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(token))

    def returnn(self):
        self.frames.pop()

    def pop(self):
        self.frame.pop()

    def slookupswitch(self, default, npairs, *pairs):
        key = self.frame.pop()
        for pair in pairs:
            match, offset = pair
            if key == match:
                return utils.signed2(offset)
            elif key < match:
                return utils.signed2(default)
        return utils.signed2(default)

    def sshr(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        s = value2 & 0x1f
        self.frame.push(value1 >> s)

    def sand(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        self.frame.push(value1 & value2)
