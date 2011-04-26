class JavaCardClassType(object):
    """
    utilities functions for a Javacard class
    """
    fields = {}
    
    def setFieldAt(self, index, value):
        self.fields[index] = value
        
    def getFieldAt(self, index):
        return self.fields[index]

class JavaCardClass(object):
    """
    This represent a JavaCard class as internal to the CAP file.
    """
    def __init__(self, offset, cap_file, resolver):
        """
        The only stuff we fot from the CP is the offset
        """
        self.offset = offset
        self._feedFromCAP(cap_file, resolver)
        
    def _feedFromCAP(self, cap_file, resolver):
        """
        The goal here is to extract all the stuff we need from the cap_file's 
        class_info stuff.
        """
        class_info = cap_file.Class.classes[self.offset]
        # And now, we want to extract the stuff
        sup_ref = class_info.super_class_ref
        self.super = resolver.resolveClass(sup_ref, cap_file)

        # create our class type
        self.cls = type("randomname", (self.super.cls,JavaCardClassType,), {})

class PythonClass(object):
    """
    This is a class that is not in the CAP file. Thus likely to be implemented
    in Python.
    """
    def __init__(self, cls):
        self.cls = cls
