import json

from utils import a2d

from refcollection import refCollection
from pymethod import PythonMethod
from jcmethod import JavaCardMethod

class linkResolver(object):
    """
    This is our link resolver. Its goal is to feed the interpeter with values
    it can understand. Those are either PythonMethod or JavaCardMethod.

    Note: We don't care (yet ?) of version of packages ...
    """
    def __init__(self, version=(3,0,1)):
        # load preprocessed pickle from all the exp files
        f = open({(3,0,1): '3.0.1.json'}[version])
        struct = json.loads(f.read())
        self.refs = {}
        for pkg in struct:
            self.refs[a2d(pkg['AID'])] = refCollection.impoort(pkg)

    def linkToCAP(self, cap_file):
        """
        Incorporate information from the CAPFile so that we can resolve indexes
        """
        self.constant_pool = cap_file.ConstantPool.constant_pool
        self.aidmap = {}
        for i in xrange(cap_file.Import.count):
            self.aidmap[i] = a2d(cap_file.Import.packages[i].aid)

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

    def resolveClass(self, aid, token):
        """ return a python class corresponding to the token """
        pkg = self.refs[aid]
        clsname = pkg.getClassName(token)
        # get the module
        mod = self._getModule(pkg.name.replace('/', '.'))
        # get the class
        return getattr(mod, clsname)

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
        method = getattr(cls, mtdname)
        return PythonMethod(mtdname, mtd['type'], method)

    def resolveIndex(self, index):
        """
        Reslove an item in the ConstantPool
        """
        cst = self.constant_pool[index]
        if cst.tag == 1:
            if cst.isExternal:
                return self.resolveClass(self.aidmap[cst.package_token], cst.class_token)
            else:
                # internal class ...
                pass
        elif cst.tag == 2:
            pass # instance fields
        elif cst.tag == 3:
            pass # virtual method
        elif cst.tag == 4:
            pass # super method
        elif cst.tag == 5:
            pass # ststic field
        elif cst.tag == 6:
            # static method
            if cst.isExternal:
                return self._resolveExtStaticMethod(self.aidmap[cst.static_method_ref.package_token],
                                                    cst.static_method_ref.class_token,
                                                    cst.static_method_ref.token)
            else:
                return JavaCardMethod(cst.static_method_ref.offset)
        else:
            assert False, cst.tag + "Is of wrong type"

    def resolvefield(self, aid, cls, token):
        """ return a python field corresponding to the tokens """
        pass

