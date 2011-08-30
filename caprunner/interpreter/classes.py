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


def findCPIndexFromClassRef(class_ref, cap_file):
    for index in xrange(cap_file.ConstantPool.count):
        cst = cap_file.ConstantPool.constant_pool[index]
        if cst.tag == 1: # ClassRef
            if class_ref.isExternal == cst.isExternal: # match
                if cst.isExternal:
                    if ((cst.class_ref.package_token == class_ref.class_ref.package_token) and 
                        (cst.class_ref.class_token == class_ref.class_ref.class_token)):
                        return index
                else:
                    if cst.class_ref == class_ref.class_ref:
                        return index
    return -1

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
        idx = findCPIndexFromClassRef(sup_ref, cap_file)
        if idx == -1:
            self.super = resolver.resolveClass(sup_ref, cap_file)
        else:
            self.super = resolver.resolveIndex(idx, cap_file)

        # create our class type
        self.cls = type("class%d"%self.offset, 
                        (self.super.cls,JavaCardClassType,), {})
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
