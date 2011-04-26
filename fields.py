class JavaCardField(object):
    """
    This is a field of a class
    It is important that this field be cached in order to keep its value
    """
    def __init__(self, clsoffset, token, cap_file):
        self.cloffset = clsoffset
        self.token = token
        self._feedFromCAP(cap_file)
        self.objref = None

    def _feedFromCAP(self, cap_file):
        # First I want to know the class
        self.cls = cap_file.Class.classes[self.cls_ofset]
        for cls in cap_file.Descriptor.classes:
            for fld in cls.fields:
                if fld.offset
        type = cap_file.Descriptor
        self._val = {'': 0}[type]

    def bindTo(self, objectref):
        self.objref = objectref

    def set(self, val):
        assert self.objref, "Field not bound to an object"
        self._val = val
        
    def get(self):
        assert self.objref, "Field not bound to an object"
        return self._val

class PythonField(object):
    """
    This is a python field.
    obj may be an object instance or a class (for static fields)
    """
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name

    def set(self, val):
        setattr(self.obj, self.name, val)

    def get(self):
        return getattr(self.obj, self.name)
