from fields import JavaCardField

class JavaCardMethodType(object):
    def __init__(self, method_descriptor_info):
        self.mdi = method_descriptor_info

class JavaCardClassType(object):
    """
    utilities functions for a Javacard class
    """
    fields = {}
    methods = {}
    def setFieldAt(self, token, value):
        self.fields[token].setValue(value)
        
    def getFieldAt(self, token):
        return self.fields[token].getValue()

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
        assert self.class_descriptor_info, "Not found in the Descriptor Conponent"
        # And now, we want to extract the stuff
        sup_ref = class_info.super_class_ref
        self.super = resolver.resolveClass(sup_ref, cap_file)

        # create our class type
        self.cls = type("randomname", (self.super.cls,JavaCardClassType,), {})
        # We put a ref to ourself in the created class ...
        self.cls._ref = self
        # I should now add the fields and the methods to the class object
        for fld in self.class_descriptor_info.fields:
            self.cls.fields[fld.token] = JavaCardField(fld)
        for mtd in self.class_descriptor_info.methods:
            self.cls.methods[mtd.token] = JavaCardMethodType(mtd)

class PythonClass(object):
    """
    This is a class that is not in the CAP file. Thus likely to be implemented
    in Python.
    """
    def __init__(self, cls):
        self.cls = cls
