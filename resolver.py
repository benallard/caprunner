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
        pass

    def resolveStaticMethod(self, aid, cls, token):
        """ return a python method corrsponding to the tokens """
        if not self.hasPackage(aid):
            return
        return self.refs[aid].getStaticMethod(cls, token)
        

    def resolvefield(self, aid, cls, token):
        """ return a python field corresponding to the tokens """
        pass

if __name__ == "__main__":
    import sys
    from exportfile import ExportFile
    rslvr = linkResolver()
    if len(sys.argv) > 1 : rslvr.addExportFile(ExportFile(open(sys.argv[1]).read()))
    print rslvr.hasPackage('\xa0\x00\x00\x00b\x00\x01')
    print rslvr.hasPackage('\xa0')

