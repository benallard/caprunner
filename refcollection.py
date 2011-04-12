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

        def addStaticMethod(self, token, name):
            assert not token in self.staticmethods
            self.staticmethods[token] = name

    def __init__(self, export_file):
        CP = export_file.constant_pool
        self.AID = export_file.AID
        self.name = str(CP[CP[export_file.this_package].name_index])
        self.classes = {}
        self.populate(export_file)

    def addClass(self, cls, CP):
        assert not cls.token in self.classes
        clsname = str(CP[CP[cls.name_index].name_index])
        clsname = clsname.split('/')[-1:]
        self.classes[cls.token] = classRefCollection(cls.token, clsname)
        self.addclassFields(cls, CP)
        self.addclassMethods(cls, CP)

    def addclassFields(self, cls, CP):
        names = []
        for fld in cls.fields:
            tmp[fld.token] = fld
            if fld.token == 0xFF:
                # compile time constant field
                # not interesting
                continue
            fldname = clsname + "." + str(CP[fld.name_index])
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
        names = []
        for mtd in cls.methods:
            tmp[mtd.token] = mtd
            mtdname = clsname + "." + str(CP[mtd.name_index])
            if mtdname in names:
                # name alread taken, so take extra steps
                if mtdname in refs:
                    # put it under another name (+$descriptor)
                    clstk, mtdtk = refs[mtdname]
                    del refs[mtdname]
                    refs['$' + mtdname + '$' + str(CP[tmp[mtdtk].descriptor_index])] = (cls.token, mtdtk)
                refs['$' + mtdname + '$' + str(CP[mtd.descriptor_index])] = (cls.token, mtd.token)
            else:
                refs[mtdname] = (cls.token, mtd.token)
            names.append(mtdname)

    def addStaticMethod(self, clstoken, token, name):
        self.classes[clstoken].addStaticMethod(token, name)

    def populate(self, export_file):
        for cls in self.classes:
            tmp = {}
            print clsname

            self.addClass(cls.token, clsname)

def process(exp, options):
    if options.pretty_print:
        exp.pprint()
    return exp.AID, refCollection(exp)

def main():
    from utils import a2d
    import os, pickle
    from exportfile import ExportFile
    from optparse import OptionParser

    parser = OptionParser(usage = "usage: %prog [options] PATH [PATH...]",
                          description = """\
This will process export file as generated by the Javacard converter.

The given path will be processed depending if it is a directory or a file.
If a directory all the export file found in the directory will be processed.
""")

    parser.add_option("-d", "--dump",
                      help    = "Dump the processed result to a pickle file.")

    parser.add_option("-P", "--pretty-print", default=False,
                      action="store_true", help= "Pretty print the results")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        return

    res = {}

    for path in args:
        if os.path.isdir(path):
            for dirname, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    if filename.endswith('.exp'):
                        # Good to go !
                        f = open(os.path.join(dirname, filename))
                        exp = ExportFile(f.read())
                        aid, refs = process(exp, options)
                        res[a2d(aid)] = refs
        else:
            f = open(path)
            exp = ExportFile(f.read())
            aid, refs = process(exp, options)
            res[a2d(aid)] = refs
    if options.dump is not None:
        f = open(options.dump, 'wb')
        pickle.dump(res, f)

if __name__ == "__main__":
    main()
