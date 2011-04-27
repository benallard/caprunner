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
