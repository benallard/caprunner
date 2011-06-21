import python.lang

from caprunner import bytecode, utils

from caprunner.interpreter.methods import PythonStaticMethod, JavaCardStaticMethod, PythonVirtualMethod, JavaCardVirtualMethod

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
        self.log = ""

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

    def echo(self, string):
        return # This greatly improve the performances !
        msg = "  " * len(self.frames) + str(string)
        self.log += msg + '\n'
    
    def step(self):
        code = self.frame.bytecodes[self.frame.ip:]
        # get the function
        f = getattr(self, bytecode.opname[code[0]])
        # get the params
        size, params = bytecode.getParams(code)
        # execute the function
        frame = self.frame
        inc = None
        self.echo("%s %s" % (bytecode.opname[code[0]], params))
        self.echo(frame.stack)
        #self.echo(frame.locals)
        try:
            inc = f(*params)
        except Exception, e:
            self.echo("caught exception: %s" % type(e))
            while not isinstance(self.frame, DummyFrame):
                for handler in self.frame.handlers:
                    if self.frame.ip in handler:
                        if handler.match(e):
                            self.echo("exception handled: ip = ", handler.handler_offs)
                            self.frame.ip = handler.handler_offs
                            self.frame.push(e)
                            return
                        if handler.last:
                            break
                self.echo("%d local handlers exhausted poping frame" % len(self.frame.handlers))
                self.frames.pop()
            # not handled, re-raise
            self.echo("exception not handled, re-raising")
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

    def _invokestaticjava(self, method):
        """
        The resolver only gave us an empty JavaCardMethod. we first need
        to fill it with informations from the rest of te CAPFile, then push
        a new frame on top of the frame stack and we're done
        """
        # ouch, what happend to the int parameters ?
        params = self._popparams(method.nargs)
        self.frames.push(JavaCardFrame(params.asArray(), method.bytecodes, method.excpt_handlers))

    def _invokestaticnative(self, method):
        """ method is of type PythonMethod """
        # pop the params
        params = self._popparams(len(method.params))
        # call the method
        ret = method(*params.asArray())
        # push the returnvalue
        self._pushretval(ret, method.retType)

    def invokestatic(self, index):
        try:
            method = self.resolver.resolveIndex(index, self.cap_file)
        except KeyError:
            # AID not known
            pass
        if isinstance(method, PythonStaticMethod):
            self._invokestaticnative(method)
        elif isinstance(method, JavaCardStaticMethod):
            self._invokestaticjava(method)

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
        elif isinstance(method, JavaCardVirtualMethod):
            self._invokevirtualjava(method)
        else:
            raise NotImplementedError

    def _invokevirtualnative(self, method):
        params = self._popparams(len(method.params))
        objref = self.frame.pop()
        if objref is None:
            raise python.lang.NullPointerException()
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

    def invokeinterface(self, nargs, index, methodtoken):
        cst = self.cap_file.ConstantPool.constant_pool[index]
        aid = self.cap_file.Import.packages[cst.class_ref.package_token].aid
        clstoken = cst.class_ref.class_token
        method = self.resolver.resolveExtInterfaceMethod(aid,
                                                          clstoken,
                                                          methodtoken)
        self._invokevirtualnative(method)

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

    def baload(self):
        index = self.frame.pop()
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

    saload = baload
    aaload = baload

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

    def sneg(self):
        val = self.frame.pop()
        self.frame.push((-val) & 0xffff)

    def bspush(self, byte):
        self.frame.push(utils.signed1(byte))

    def s2b(self):
        val = self.frame.pop()
        self.frame.push(utils.signed1(val & 0xff))

    def sreturn(self):
        val = self.frame.pop()
        self.frames.pop()
        self.frame.push(val)

    areturn = sreturn

    def smul(self):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        self.frame.push((val1 * val2) & 0xffff)

    def sdiv(self):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        self.frame.push((val1 // val2) & 0xffff)

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

    def ifnull(self, branch):
        val = self.frame.pop()
        if val is None:
            return utils.signed1(branch)

    def ifnonnull(self, branch):
        val = self.frame.pop()
        if val is not None:
            return utils.signed1(branch)

    def _ifxx_w(self, branch, op):
        val = self.frame.pop()
        if {'eq': val == 0,
            'ne': val != 0,
            'lt': val < 0,
            'le': val <= 0,
            'gt': val > 0,
            'ge': val >= 0}[op]:
            return utils.signed2(branch)
    def ifeq_w(self, branch):
        return self._ifxx_w(branch, 'eq')
    def ifne_w(self, branch):
        return self._ifxx_w(branch, 'ne')
    def iflt_w(self, branch):
        return self._ifxx_w(branch, 'lt')
    def ifle_w(self, branch):
        return self._ifxx_w(branch, 'le')
    def ifgt_w(self, branch):
        return self._ifxx_w(branch, 'gt')
    def ifge_w(self, branch):
        return self._ifxx_w(branch, 'ge')

    def ifnull_w(self, branch):
        val = self.frame.pop()
        if val is None:
            return utils.signed2(branch)

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

    def _if_acmpxx(self, branch, op):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        if {'eq': val1 is val2,
            'ne': val1 is not val2}[op]:
            return utils.signed1(branch)

    def if_acmpeq(self, branch):
        return self.if_acmpxx(branch, 'eq')
    def if_acmpne(self, branch):
        return self.if_acmpxx(branch, 'ne')

    def _if_scmpxx_w(self, branch, op):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        if {'eq': val1 == val2,
            'ne': val1 != val2,
            'lt': val1 < val2,
            'le': val1 <= val2,
            'gt': val1 > val2,
            'ge': val1 >= val2}[op]:
            return utils.signed2(branch)

    def if_scmpeq_w(self, branch):
        return self._if_scmpxx_w(branch, 'eq')
    def if_scmpne_w(self, branch):
        return self._if_scmpxx_w(branch, 'ne')
    def if_scmplt_w(self, branch):
        return self._if_scmpxx_w(branch, 'lt')
    def if_scmple_w(self, branch):
        return self._if_scmpxx_w(branch, 'le')
    def if_scmpgt_w(self, branch):
        return self._if_scmpxx_w(branch, 'gt')
    def if_scmpge_w(self, branch):
        return self._if_scmpxx_w(branch, 'ge')

    def _if_acmpxx_w(self, branch, op):
        val2 = self.frame.pop()
        val1 = self.frame.pop()
        if {'eq': val1 is val2,
            'ne': val1 is not val2}[op]:
            return utils.signed2(branch)

    def if_acmpeq_w(self, branch):
        return self._if_acmpxx_w(branch, 'eq')
    def if_acmpne_w(self, branch):
        return self._if_acmpxx_w(branch, 'ne')

    def goto(self, branch):
        return utils.signed1(branch)

    def goto_w(self, branch):
        return utils.signed2(branch)

    def jsr(self, branch):
        self.frame.push(self.frame.ip+3)# jsr-branch1-branch2 = 3
        return utils.signed2(branch)

    def ret(self, index):
        return self.frame.locals[index] - self.frame.ip

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

    def _xastore(self):
        value = self.frame.pop()
        index = self.frame.pop()
        arrayref = self.frame.pop()
        # we should check index validity
        arrayref[index] = value

    bastore = _xastore
    aastore = _xastore
    sastore = _xastore

    def sinc(self, index, const):
        self.frame.locals[index] += utils.signed1(const)
        

    def sspush(self, short):
        self.frame.push(utils.signed2(short))

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

    def anewarray(self, index):
        count = utils.signed2(self.frame.pop())
        if count < 0:
            raise python.lang.NegativeArraySizeException()
        # We don't really care of the type of the elements
        array = [None for i in xrange(count)]
        self.frame.push(array)

    def arraylength(self):
        arrayref = self.frame.pop()
        self.frame.push(len(arrayref))

    def dup(self):
        value = self.frame.pop()
        self.frame.push(value)
        self.frame.push(value)

    def dup2(self):
        word1 = self.frame.pop()
        word2 = self.frame.pop()
        self.frame.push(word2)
        self.frame.push(word1)
        self.frame.push(word2)
        self.frame.push(word1)

    def dup_x(self, mn):
        m = (mn & 0xf0) >> 4
        n = (mn & 0x0f)
        if n == 0:
            # special case of n == 0 means n == m
            n = m
        ops = [self.frame.pop() for i in xrange(m)]
        n = n - m
        ext_ops = [self.frame.pop() for i in xrange(n)]
        # simply duplicate them on top
        self.frame.stack.extend(reversed(ops))
        self.frame.stack.extend(reversed(ext_ops))
        self.frame.stack.extend(reversed(ops))

    def swap_x(self, mn):
        m = (mn & 0xf0) >> 4
        n = (mn & 0x0f)
        opsm = [self.frame.pop() for i in xrange(m)]
        opsn = [self.frame.pop() for i in xrange(n)]
        self.frame.stack.extend(reversed(opsn))
        self.frame.stack.extend(reversed(opsm))

    def putfield_s(self, index):
        value = self.frame.pop()
        objref = self.frame.pop()
        (clsref, token) = self.resolver.resolveIndex(index, self.cap_file)
        objref.setFieldAt(clsref, token, value)

    putfield_a = putfield_s
    putfield_b = putfield_s

    def putstatic_a(self, index):
        value = self.frame.pop()
        field = self.resolver.resolveIndex(index, self.cap_file)
        field.set(value)

    def getfield_b_this(self, index):
        ''' b is for byte, not boolean'''
        objref = self.frame.aget(0)
        (clsref, token) = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(clsref, token))

    def getfield_s_this(self, index):
        objref = self.frame.aget(0)
        (clsref, token) = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(clsref, token) or 0)

    def getfield_a_this(self, index):
        objref = self.frame.aget(0)
        (clsref, token) = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(clsref, token) or None)

    def getfield_a(self, index):
        objref = self.frame.pop()
        (clsref, token) = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(clsref, token) or None)

    def getfield_s(self, index):
        objref = self.frame.pop()
        (clsref, token) = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(objref.getFieldAt(clsref, token) or 0)

    getfield_b = getfield_s

    def getstatic_a(self, index):
        field = self.resolver.resolveIndex(index, self.cap_file)
        self.frame.push(field.get() or None)

    def returnn(self):
        self.frames.pop()

    def pop(self):
        self.frame.pop()

    def pop2(self):
        self.frame.pop()
        self.frame.pop()

    def slookupswitch(self, default, npairs, *pairs):
        key = self.frame.pop()
        for pair in pairs:
            match, offset = pair
            match = utils.signed2(match)
            if key == match:
                return utils.signed2(offset)
            elif key < match:
                return utils.signed2(default)
        return utils.signed2(default)

    def stableswitch(self, default, low, high, *offsets):
        index = self.frame.pop()
        try:
            return utils.signed2(offsets[index - low])
        except IndexError:
            return utils.signed2(default)

    def sshr(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        s = value2 & 0x1f
        self.frame.push((value1 >> s) & 0xffff)

    def sshl(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        s = value2 & 0x1f
        self.frame.push((value1 << s) & 0xffff)

    def sushr(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        s = value2 & 0x1f
        if value1 >= 0:
            self.frame.push((value1 >> s) & 0xffff)
        else:
            self.frame.push(((value1 >> s) + (2 << ~s)) & 0xffff)

    def sand(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        self.frame.push(value1 & value2)

    def sor(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        self.frame.push(value1 | value2)

    def sxor(self):
        value2 = self.frame.pop()
        value1 = self.frame.pop()
        self.frame.push(value1 ^ value2)

    def checkcast(self, atype, index):
        objectref = self.frame.pop()
        self.frame.push(objectref)
        # First determine type to check against
        types = {10: bool, 11: int, 12: int, 13: int}
        if atype in types:
            type = types[atype]
        else:
            type = self.resolver.resolveIndex(index, self.cap_file).cls
        # Then check it ...
        if atype == 14:
            if not isinstance(objectref, list):
                raise python.lang.ClassCastException
            for elem in objectref:
                if not isinstance(elem, list):
                    raise python.lang.ClassCastException
        else:
            if not isinstance(objectref, type):
                raise python.lang.ClassCastException
            
