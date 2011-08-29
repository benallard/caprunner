from caprunner import utils

class JavaCardField(object):
    """
    This is a field of a class
    It is important that this field be cached in order to keep its value
    """
    def __init__(self, field_descriptor_info):
        self.fdi = field_descriptor_info
        self._val = None

    def setValue(self, val):
        self._val = val
        
    def getValue(self):
        return self._val

    def __str__(self):
        return str(self._val)
    __repr__ = __str__

class JavaCardStaticField(object):
    def __init__(self, offset, cap_file, resolver):
        self.offset = offset
        print "I am field", offset
        sf = cap_file.StaticField
        if offset < sf.array_init_count * 2:
            offset = offset // 2
            aii = sf.array_init[offset]
            convertfunc = {2: lambda x: bool(x[0]), 
                           3: lambda x: utils.signed1(x[0]), 
                           4: lambda x: utils.signed2(x[0] << 8 + x[1]), 
                           5: lambda x: utils.signed4(x[0] << 24 + x[1] << 16 + x[2] << 8 + x[3])
                           }[aii.type]
            elemsize = {2: 1, 3: 1, 4: 2, 5: 4}[aii.type]
            index = 0
            value = []
            while index < aii.count:
                value.append(convertfunc(aii.values[index:]))
                index += elemsize
            self.val = value
        elif offset < sf.reference_count * 2:
            self.val = None
        else:
            offset -= sf.reference_count * 2
            if offset <= sf.default_value_count:
                self.val = None
            else:
                print "I am a non-default primitive type"
                raise NotImplementedError("non default primitive static field")

    def set(self, value):
        self.val = value

    def get(self):
        return self.val

class PythonField(object):
    """
    This is a python field.
    obj may be an object instance or a class (for static fields)
    """
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name

    def setValue(self, val):
        setattr(self.obj, self.name, val)

    def getValue(self):
        return getattr(self.obj, self.name)
