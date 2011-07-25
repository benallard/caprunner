import copy
from fields import JavaCardField

class NoSuchClass(Exception):
    pass

class JavaCardMethodType(object):
    def __init__(self, method_descriptor_info):
        self.mdi = method_descriptor_info

def makefieldmine(f):
    """ 
    All fields are created on the class object.
    They shall not be modified on this object, but on this instance !
    So we need to make them property of the instance itself.
    """
    def wrapper(self, cls, token, *params):
        if getattr(self, 'fields', None) is None:
            self.fields = {}
        idx = token + self.fieldoffsets[cls]
        if idx not in self.fields:
            self.fields[idx] = copy.deepcopy(self.clsfields[idx])
        return f(self, cls, token, *params)
    return wrapper

class JavaCardClassType(object):
    """
    utilities functions for a Javacard class
    """
    @makefieldmine
    def setFieldAt(self, cls, token, value):
        self.fields[token + self.fieldoffsets[cls]].setValue(value)
        
    @makefieldmine
    def getFieldAt(self, cls, token):
        return self.fields[token + self.fieldoffsets[cls]].getValue()

class JavaCardClass(object):
    """
    This represent a JavaCard class as internal to the CAP file.
    """
    def __init__(self, offset, cap_file, resolver):
        """
        The only stuff we got from the CP is the offset
        """
        self.offset = offset
        self._feedFromCAP(cap_file, resolver)
        
    def _feedFromCAP(self, cap_file, resolver):
        """
        The goal here is to extract all the stuff we need from the cap_file's 
        class_info stuff.
        """
        class_info = cap_file.Class.classes[self.offset]
        self.class_descriptor_info = None
        for cls in cap_file.Descriptor.classes:
            if cls.this_class_ref.class_ref == self.offset:
                self.class_descriptor_info = cls
                break
        if self.class_descriptor_info is None:
            raise NoSuchClass(self.offset)
        # And now, we want to extract the stuff
        sup_ref = class_info.super_class_ref
        self.super = resolver.resolveClass(sup_ref, cap_file)

        # create our class type
        self.cls = type("class%d"%self.offset, (self.super.cls,JavaCardClassType,), {})
        # We put a ref to ourself in the created class ...
        self.cls._ref = self
        if not isinstance(self.super, JavaCardClass):
            self.cls.clsfields = []
            self.cls.fieldoffsets = {}

        fieldoffset = len(self.cls.clsfields)
        self.cls.fieldoffsets[self.offset] = fieldoffset
        # I should now add the fields and the methods to the class object.
        for fld in self.class_descriptor_info.fields:
            if not fld.isStatic:
                self.cls.clsfields.append(JavaCardField(fld))
                # this check that we are adding them sequentially
                assert len(self.cls.clsfields) == fld.token + fieldoffset + 1

class PythonClass(object):
    """
    This is a class that is not in the CAP file. Thus likely to be implemented
    in Python.
    """
    def __init__(self, cls):
        self.cls = cls

    def __str__(self):
        return "<PythonClass: %s>" % str(self.cls)
