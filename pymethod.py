class PythonMethod(object):
    """
    This is the Python version of the JavaCardMethod
    We need to know the parameters, their number and types
    We also need to know if the function returns something
    """
    def __init__(self, refCollection, clstoken, token, isStatic=False):
        """ The refCollection is an improved version of the export file """
        if isStatic:
            mtd = refCollection.getstaticmethod(clstoken, token)
        else:
            mtd = refCollection.getvirtualmethod(clstoken, token)

    def __call__(self, *params):
        return self.method(*params)
