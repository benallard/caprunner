import json

from utils import a2d

from caprunner.refcollection import refCollection
from caprunner.interpreter.fields import JavaCardStaticField
from caprunner.interpreter.methods import PythonStaticMethod, JavaCardStaticMethod, PythonVirtualMethod, JavaCardVirtualMethod
from caprunner.interpreter.classes import PythonClass, JavaCardClass

def cacheresult(f):
    """
    Caching for the resolver
    Quick test shown that it is not efficient ... :(
    Anyway, this is at least necessary for the fields ... That twice the same
    request returns the same field.
    """
    __cache = {}
    def wrapper(self, index, cap_file):
        try:
            pkg = __cache[a2d(cap_file.Header.package.aid)]
        except KeyError:
            __cache[a2d(cap_file.Header.package.aid)] = {}
            pkg = __cache[a2d(cap_file.Header.package.aid)]
        try:
            return pkg[index]
        except KeyError:
            pkg[index] = f(self, index, cap_file)
            return pkg[index]
    return wrapper

class linkResolver(object):
    """
    This is our link resolver. Its goal is to feed the interpeter with values
    it can understand.
    Note: We don't care (yet ?) of version of packages ...
    """
    def __init__(self, version=(3,0,1)):
        # load preprocessed pickle from all the exp files
        f = open({(3,0,1): '3.0.1.json'}[version])
        struct = json.loads(f.read())
        self.refs = {}
        for pkg in struct:
            self.refs[a2d(pkg['AID'])] = refCollection.impoort(pkg)

    def _getModule(self, name):
        if name.startswith('java'):
            try:
                # pythoncard begins with python ...
                mod = __import__('python'+name[4:])
            except ImportError:
                mod = __import__(name)
        else:
            mod = __import__(name)
        for comp in name.split('.')[1:]:
            mod = getattr(mod, comp)
        return mod

    def addExportFile(self, exp):
        """
        Add a non-standard (not javacard) export file references
        """
        self.refs[a2d(exp.AID)] = refCollection.from_export_file(exp)

    def hasPackage(self, aid):
        """ return if a python package corresponding to the aid is known """
        return aid in self.refs

    def resolveClass(self, cst, cap_file):
        if cst.isExternal:
            pkg = cap_file.Import.packages[cst.class_ref.package_token]
            return self._resolveExtClass(a2d(pkg.aid),
                                         cst.class_ref.class_token)
        else:
            # internal class ...
            return JavaCardClass(cst.class_ref, cap_file, self)

    def _resolveExtClass(self, aid, token):
        """ return a python class corresponding to the token """
        pkg = self.refs[aid]
        clsname = pkg.getClassName(token)
        # get the module
        mod = self._getModule(pkg.name.replace('/', '.'))
        # get the class
        return PythonClass(getattr(mod, clsname))

    def resolveStaticMethod(self, cst, cap_file):
        if cst.isExternal:
            pkg = cap_file.Import.packages[cst.static_method_ref.package_token]
            return self._resolveExtStaticMethod(
                a2d(pkg.aid),
                cst.static_method_ref.class_token,
                cst.static_method_ref.token)
        else:
            return JavaCardStaticMethod(cst.static_method_ref.offset, cap_file, self)

    def _resolveExtStaticMethod(self, aid, cls, token):
        """
        Resolve an external static method
        return a python method corrsponding to the tokens 
        """
        pkg = self.refs[aid]
        (clsname, mtd) = pkg.getStaticMethod(cls, token)
        mtdname = mtd['name']
        # get the module
        mod = self._getModule(pkg.name.replace('/', '.'))
        # get the class
        cls = getattr(mod, clsname)
        # get the method
        if '<init>' in mtdname:
            mtdname = '__init__' + mtdname[6:]
        try:
            method = getattr(cls, mtdname)
        except AttributeError:
            print "Cannot find %s in %s in %s" % (mtdname, clsname, pkg.name)
            raise
        return PythonStaticMethod(mtdname, mtd['type'], method)

    def resolveStaticField(self, cst, cap_file):
        if cst.isExternal:
            pkg = cap_file.Import.packages[cst.static_field_ref.package_token]
            return self._resolveExtStaticField(
                a2d(pkg.aid),
                cst.static_field_ref.class_token,
                cst.static_field_ref.token)
        else:
            return JavaCardStaticField(cst.static_field_ref.offset, cap_file, self)

    def _resolveExtStaticField(self, aid, cls, token):
        """
        Resolve an external static field
        return a python method corrsponding to the tokens
        Cannot really test it actually ...
        """
        pkg = self.refs[aid]
        (clsname, fld) = pkg.getStaticField(cls, token)
        fldname = fld['name']
        # get the module
        mod = self._getModule(pkg.name.replace('/', '.'))
        # get the class
        cls = getattr(mod, clsname)
        field = getattr(cls, fldname)
        return PythonStaticField(fldname, fld['type'], field)

    def resolveVirtualMethod(self, cst, cap_file):
        if cst.isExternal:
            pkg = cap_file.Import.packages[cst.class_ref.package_token]
            return self._resolveExtVirtualMethod(a2d(pkg.aid),
                                                 cst.class_ref.class_token,
                                                 cst.token)
        else:
            # it is fully already resolved from the other side, we just need
            # the token
            return JavaCardVirtualMethod(cst.class_ref, cst.token, cap_file, self)

    def _resolveExtVirtualMethod(self, aid, cls, token):
        pkg = self.refs[aid]
        (clsname, mtd) = pkg.getVirtualMethod(cls, token)
        mtdname = mtd['name']
        if mtdname[0] == '$':
            # Call every variations of the function the same way
            mtdname = mtdname[1:mtdname[1:].find('$') + 1]
        return PythonVirtualMethod(mtdname, mtd['type'])

    @cacheresult
    def resolveIndex(self, index, cap_file):
        """
        Resolve an item in the ConstantPool
        """
        cst = cap_file.ConstantPool.constant_pool[index]
        if cst.tag == 1: # class
            return self.resolveClass(cst, cap_file)
        elif cst.tag == 2: # instance fields
            return cst.token
        elif cst.tag == 3: # virtual method
            return self.resolveVirtualMethod(cst, cap_file)
        elif cst.tag == 4:
            raise NotImplementedError
            pass # super method
        elif cst.tag == 5: # static field
            return self.resolveStaticField(cst, cap_file)
        elif cst.tag == 6: # static method
            return self.resolveStaticMethod(cst, cap_file)
        else:
            assert False, cst.tag + "Is of wrong type"

