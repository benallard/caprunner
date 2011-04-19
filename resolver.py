import json

from utils import a2d

from refcollection import refCollection

class linkResolver(object):
    """
    We don't take care of version of packages ...
    """
    def __init__(self, version=(3,0,1)):
        self.version = version
        # load preprocessed pickle from all the exp files
        f = open({(3,0,1): '3.0.1.json'}[self.version])
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

    def resolveClass(self, aid, token):
        """ return a python class corresponding to the token """
        pkg = self.refs[aid]
        clsname = pkg.getClassName(token)
        # get the module
        mod = self._getModule(pkg.name.replace('/', '.'))
        # get the class
        return getattr(mod, clsname)

    def resolveStaticMethod(self, aid, cls, token):
        """ return a python method corrsponding to the tokens """
        pkg = self.refs[aid]
        (clsname, mtdname) = pkg.getStaticMethod(cls, token)
        # get the module
        mod = self._getModule(pkg.name.replace('/', '.'))
        # get the class
        cls = getattr(mod, clsname)
        # get the method
        return getattr(cls, mtdname)

    def resolvefield(self, aid, cls, token):
        """ return a python field corresponding to the tokens """
        pass

