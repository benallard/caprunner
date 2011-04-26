class ExceptionHandler(object):
    def __init__(self, handler_info):
        """ handler is the type found in the cap_file """
        self.handler = handler_info.handler_offset
        self.start = handler_info.start_offset
        self.stop = self.start + handler_info.active_length
        self.last = bool(handler_info.stop_bit)
        self.catch_type_offs = handler_info.catch_type_index

    def __contains__(self, ip):
        """ returns if the ip is in the range of this handler """
        return self.start < ip < self.stop

class JavaCardStaticMethod(object):
    """
    The goal of this class is to make things easier for the JavaCardFrame
    This class would embed the parameters, the bytecode and the exception 
    handlers (more might come later)
    """
    def __init__(self, offset, cap_file):
        """ 
        This object is first created from information of the export_file and 
        the ConstantPool. Those only provide the offset in the Method 
        Component in case of internal references.
        """
        self.offset = offset
        self._feedFromCAP(cap_file)

    def _feedFromCAP(self, cap_file):
        """ 
        We init it from components of the cap_file
        """
        # Get the methodInfo is not too complicated
        self.methodinfo = cap_file.Method.methods[self.offset]
        # Now, we also'd like the MethodDescriptorInfo
        self.methoddescriptorinfo = None
        for cls in cap_file.Descriptor.classes:
            for mtd in cls.methods:
                if mtd.method_offset == self.offset:
                    # Bingo !
                    self.methoddescriptorinfo = mtd
                    break
        assert self.methoddescriptorinfo is not None, "Method Not found in Descriptor Component"
        mdi = self.methoddescriptorinfo
        # We now care about the exception handlers
        self.excpt_handlers = []
        for hdlr in xrange(mdi.exception_handler_index, 
                           mdi.exception_handler_index + 
                           mdi.exception_handler_count):
            self.excpt_handlers.append(ExceptionHandler(
                    cap_file.Method.exception_handlers[hdlr], cap_file))
        # I first want the number of arguments
        self.nargs = self.methodinfo.method_info.nargs

class PythonStaticMethod(object):
    """
    This is the Python version of the JavaCardMethod
    We need to know the parameters, their number and types
    We also need to know if the function returns something
    """
    def __init__(self, name, typ, method):
        self.name = name
        self.type = typ
        self.method = method
        self._analyseType(typ)

    def _getTypes(self, string):
        res = []
        strtype = ''
        while len(string) > 0:
            if string[0] == 'B':
                strtype += 'boolean'
                size = 1
            elif string[0] == 'I':
                strtype += 'integer'
                size = 1
            elif string[0] == 'S':
                strtype += 'short'
                size = 1
            elif string[0] == 'Z':
                string = string[1:]
                end = string.find(';')
                strtype += 'ref of '+string[:end - 1]
                size = end
            elif string[0] == 'V':
                strtype += 'void'
                size = 1
            elif string[0] == '[':
                strtype = 'array of '
                string = string[1:]
                continue
            else:
                assert False, string[0]+' not recognized'
            res.append(strtype)
            string = string[size:]
        return res

    def _analyseType(self, string):
        assert string[0] == '('
        # First analyse the params
        self.params = self._getTypes(string[1:string.find(')')])
        self.retType = self._getTypes(string[string.find(')') + 1:])[0]

    def __call__(self, *params):
        return self.method(*params)
