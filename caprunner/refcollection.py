from utils import a2d, d2a

class refCollection(object):
    """
    This is a processed version of the Export File for it to be easier 
    processed by python
    """

    class classRefCollection(object):
        """
        Those are the reference for a class
        """
        def __init__(self, token, name):
            self.token = token
            self.name = name
            # three kinds of methods:
            # - virtual
            # - static
            # - interface
            self.virtualmethods = {}
            self.staticmethods = {}
            self.interfacemethods = {}
            # two kinds of fields:
            # - static
            # - instance
            self.staticfields = {}
            self.instancefields = {}

        def addStaticMethod(self, token, name, type):
            assert not token in self.staticmethods
            self.staticmethods[token] = {'name':name, 'type':type}

        def getStaticMethod(self, token):
            return self.staticmethods[token]

        def addVirtualMethod(self, token, name, type):
            if "<init>" in name:
                # Arguably, constructors are statics ...
                self.addStaticMethod(token, name, type)
            else:
                assert not token in self.virtualmethods, self.virtualmethods[token]
                self.virtualmethods[token] = {'name':name, 'type':type}

        def getVirtualMethod(self, token):
            return self.virtualmethods[token]

        def addInterfaceMethod(self, token, name, type):
            assert not token in self.interfacemethods
            self.interfacemethods[token] = {'name':name, 'type':type}

        def getInterfaceMethod(self, token):
            return self.interfacemethods[token]

        def export(self):
            struct = {}
            struct['token'] = self.token
            struct['name'] = self.name
            struct['virtualmethods'] = self.virtualmethods
            struct['staticmethods'] = self.staticmethods
            struct['interfacemethods'] = self.interfacemethods
            struct['staticfields'] = self.staticfields
            struct['instancefields'] = self.instancefields
            return struct

        def _unroll(self, struct, name):
            dct = getattr(self, name)
            for token, name in struct[name].iteritems():
                dct[int(token)] = name

        @classmethod
        def impoort(cls, struct):
            slf = cls(struct['token'], struct['name'])
            
            slf._unroll(struct, 'virtualmethods')
            slf._unroll(struct, 'staticmethods')
            slf._unroll(struct, 'interfacemethods')
            slf._unroll(struct, 'staticfields')
            slf._unroll(struct, 'instancefields')
            return slf

    def __init__(self, AID, name):
        self.AID = AID
        self.name = name
        self.classes = {}

    def addClass(self, cls, CP):
        assert not cls.token in self.classes
        clsname = str(CP[CP[cls.name_index].name_index])
        clsname = clsname.split('/')[-1]
        self.classes[cls.token] = self.classRefCollection(cls.token, clsname)
        self.addclassFields(cls, CP)
        self.addclassMethods(cls, CP)

    def getClassName(self, token):
        return self.classes[token].name

    def addclassFields(self, cls, CP):
        tmp = {}
        names = []
        for fld in cls.fields:
            tmp[fld.token] = fld
            if fld.token == 0xFF:
                # compile time constant field
                # not interesting
                continue
            fldname = str(CP[fld.name_index])
            if fldname in names:
                # name alread taken, so take extra steps
                if fldname in refs:
                    # save previous under another name
                    clstk, fldtk = refs[mtdname]
                    del refs[mtdname]
                    refs['$' + mtdname + '$' + str(CP[tmp[fldtk].descriptor_index])] = (cls.token, fldtk)
                refs['$' + mtdname + '$' + str(CP[mtd.descriptor_index])] = (cls.token, fld.token)
            else:
                refs[fldname] = (cls.token, fld.token)
            name.append(fldname)

    def addclassMethods(self, cls, CP):
        tmp = []
        names = {}
        for mtd in cls.methods:
            # First pass to look for name colision (type related)
            mtdname = str(CP[mtd.name_index])
            if mtdname in tmp:
                print "colision with %s" % mtdname
                mtdname = '$' + mtdname + '$' + str(CP[mtd.descriptor_index])
                print "renamed it %s" % mtdname
                names[mtd] = mtdname
            else:
                names[mtd] = mtdname
            tmp.append(mtdname)
        tmp = {}    
        for mtd in cls.methods:
            tmp[mtd.token] = mtd
            mtdname = names[mtd]
            mtdtype = str(CP[mtd.descriptor_index])
            if cls.isInterface:
                self.addInterfaceMethod(cls.token, mtd.token, mtdname, mtdtype)
            elif mtd.isStatic:
                self.addStaticMethod(cls.token, mtd.token, mtdname, mtdtype)
            else:
                self.addVirtualMethod(cls.token, mtd.token, mtdname, mtdtype)

    def addStaticMethod(self, clstoken, token, name, type):
        self.classes[clstoken].addStaticMethod(token, name, type)

    def getStaticMethod(self, clstoken, token):
        cls = self.classes[clstoken]
        return cls.name, cls.getStaticMethod(token)

    def addVirtualMethod(self, clstoken, token, name, type):
        self.classes[clstoken].addVirtualMethod(token, name, type)

    def getVirtualMethod(self, clstoken, token):
        cls = self.classes[clstoken]
        return cls.name, cls.getVirtualMethod(token)

    def addInterfaceMethod(self, clstoken, token, name, type):
        self.classes[clstoken].addInterfaceMethod(token, name, type)

    def getInterfaceMethod(self, clstoken, token):
        cls = self.classes[clstoken]
        return cls.name, cls.getInterfaceMethod(token)

    def populate(self, export_file):
        for cls in export_file.classes:
            self.addClass(cls, export_file.constant_pool)

    def export(self):
        """ return a JSON representation of this class """
        struct = {}
        struct['AID'] = d2a(self.AID)
        struct['name'] = self.name
        struct['classes'] = {}
        for key, value in self.classes.iteritems():
            struct['classes'][key] = value.export()
        return struct

    @classmethod
    def impoort(cls, struct):
        """ return a cls type with the content of the JSON string """
        slf = cls(a2d(struct['AID']), struct['name'])
        for token, claass in struct['classes'].iteritems():
            slf.classes[int(token)] = cls.classRefCollection.impoort(claass)
        return slf
        
    @classmethod
    def from_export_file(cls, export_file):
        CP = export_file.constant_pool
        slf = cls(a2d(export_file.AID), str(CP[CP[export_file.this_package].name_index]))
        slf.populate(export_file)
        return slf
