class PythonMethod(object):
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

