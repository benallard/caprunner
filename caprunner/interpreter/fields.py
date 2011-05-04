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
            self.val = sf.array_init[offset].values
        elif offset < sf.reference_count * 2:
            self.val = None
        else:
            print "I am a primitive type"
            raise NotImplementedError("primitive static field")

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
