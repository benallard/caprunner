import os, pickle
from utils import *

class ExportFile(object):

    class CPInfo(object):
        def __init__(self, data):
            self.data = data
            self.tag = u1(data[:1])
            self.info = u1a(len(data)-1, data[1:])

        @staticmethod
        def get(data):
            return {1: ExportFile.CPInfoUtf8,
                    3: ExportFile.CPInfoInteger,
                    7: ExportFile.CPInfoClassref,
                    13: ExportFile.CPInfoPackage
                    }[u1(data[:1])](data)

    class CPInfoUtf8(CPInfo):
        def __init__(self, data):
            ExportFile.CPInfo.__init__(self, data)
            self.length = u2(data[1:3])
            self.bytes = u1a(self.length, data[3:])
            self.size = self.length + 3
        def __str__(self):
            return ''.join([chr(c) for c in self.bytes])

    class CPInfoInteger(CPInfo):
        size = 5
        def __init__(self, data):
            ExportFile.CPInfo.__init__(self, data)
            self.bytes = u4(data[1:5])
        def __str__(self):
            return "%d" % self.bytes

    class CPInfoClassref(CPInfo):
        size = 3
        def __init__(self, data):
            ExportFile.CPInfo.__init__(self, data)
            self.name_index = u2(data[1:3])
        def __str__(self):
            return "Classref: name @%d" % self.name_index

    class CPInfoPackage(CPInfo):
        def __init__(self, data):
            ExportFile.CPInfo.__init__(self, data)
            self.flags = u1(data[1:2])
            self.name_index = u2(data[2:4])
            self.minor_version = u1(data[4:5])
            self.major_version = u1(data[5:6])
            self.aid_length = u1(data[6:7])
            self.aid = u1a(self.aid_length, data[7:])
            self.size = self.aid_length + 7 
        @property
        def version(self):
            return (self.major_version, self.minor_version)
        def __str__(self):
            return "Package: %s %s Name @%d" % (a2s(self.aid), self.version, self.name_index)

    class ClassInfo(object):
        ACC_PUBLIC  = 0x0001
        ACC_FINAL = 0x0010
        ACC_INTERFACE = 0x0200
        ACC_ABSTRACT = 0x0400
        ACC_SHAREABLE = 0x0800
        ACC_REMOTE = 0x1000
        class FieldInfo(object):
            ACC_PUBLIC = 0x0001
            ACC_PROTECTED = 0x0004
            ACC_STATIC = 0x0008
            ACC_FINAL = 0x0010
            class AttributeInfo(object):
                def __init__(self, data):
                    self.data = data
                    self.attribute_name_index = u2(self.data[:2])
                    self.attribute_length = u4(self.data[2:6])
                    self.info = u1a(self.attribute_length, self.data[6:])

            class ConstantValueAttribute(AttributeInfo):
                size = 8
                def __init__(self, data):
                    ExportFile.ClassInfo.FieldInfo.AttributeInfo.__init__(self, data)
                    self.constant_value_index = u2(self.data[6:8])
                def __str__(self):
                    return "Constant, value @%d" % self.constant_value_index

            def __init__(self, data):
                self.data = data
                self.token = u1(self.data[:1])
                self.access_flags = u2(self.data[1:3])
                self.name_index = u2(self.data[3:5])
                self.descriptor_index = u2(self.data[5:7])
                self.attributes_count = u2(self.data[7:9])
                shift = 9
                self.attributes = []
                for i in xrange(self.attributes_count):
                    data = self.data[shift:]
                    attr = self.ConstantValueAttribute(data)
                    self.attributes.append(attr)
                    shift += attr.size
                self.size = shift

        class MethodInfo(object):
            size = 7
            ACC_PUBLIC = 0x0001
            ACC_PROTECTED = 0x0004
            ACC_STATIC = 0x0008
            ACC_FINAL = 0x0010
            ACC_ABSTRACT = 0x0400
            def __init__(self, data):
                self.data = data
                self.token = u1(self.data[:1])
                self.access_flags = u2(self.data[1:3])
                self.name_index = u2(self.data[3:5])
                self.descriptor_index = u2(self.data[5:7])
                self.isStatic = bool(self.access_flag & self.ACC_STATIC)
                self.isVirtual = not self.isStatic
                # for interface information, look at the enclosing class infos
            def __str__(self):
                return "MethodInfo, name@%d, TK:%d" % (self.name_index, self.token)

        def __init__(self, data):
            self.data = data
            self.token = u1(self.data[:1])
            self.access_flags = u2(self.data[1:3])
            self.name_index = u2(self.data[3:5])
            self.export_supers_count = u2(self.data[5:7])
            self.supers = u2a(self.export_supers_count, self.data[7:])
            shift = 7 + self.export_supers_count*2
            self.export_interfaces_count = u1(self.data[shift:shift+1])
            shift += 1
            self.interfaces = u2a(self.export_interfaces_count, self.data[shift:])
            shift += self.export_interfaces_count*2
            self.export_fields_count = u2(self.data[shift:shift+2])
            self.fields = []
            shift += 2
            for i in xrange(self.export_fields_count):
                data = self.data[shift:]
                field = self.FieldInfo(data)
                self.fields.append(field)
                shift += field.size
            self.export_methods_count = u2(self.data[shift:shift+2])
            self.methods = []
            shift += 2
            for i in xrange(self.export_methods_count):
                data = self.data[shift:]
                method = self.MethodInfo(data)
                self.methods.append(method)
                shift += method.size
            self.size = shift
        def __str__(self):
            return "ClassInfo: name @%d, %d supers, %d interfaces, %d fields, %d methods (%s)" % (
                self.name_index,
                self.export_supers_count,
                self.export_interfaces_count,
                self.export_fields_count,
                self.export_methods_count,
                ', '.join([str(mtd) for mtd in self.methods]))

    def __init__(self, data):
        self.data = data
        
        self.magic = u4(self.data[:4])
        self.minor_version = u1(self.data[4:5])
        self.major_version = u1(self.data[5:6])
        self.constant_pool_count = u2(self.data[6:8])
        self.constant_pool = []
        shift = 8
        for i in xrange(self.constant_pool_count):
            data = self.data[shift:]
            cp_info = self.CPInfo.get(data)
            self.constant_pool.append(cp_info)
            shift += cp_info.size
        self.this_package = u2(self.data[shift:shift+2])
        self.export_class_count = u1(self.data[shift+2:shift+3])
        shift += 3
        self.classes = []
        for i in xrange(self.export_class_count):
            data = self.data[shift:]
            cls = self.ClassInfo(data)
            self.classes.append(cls)
            shift += cls.size
            
    @property
    def version(self):
        return (self.major_version, self.minor_version)

    def __str__(self):
        return "<ExportFile:\n\tMagic: %08X\n\tVersion: %s\n\tCstPool:\n\t\t%s\n\tThis:%s\n\tExports:\n\t\t%s\n>" % (
            self.magic,
            self.version,
            '\n\t\t'.join([str(cp_info) for cp_info in self.constant_pool]),
            self.constant_pool[self.this_package],
            '\n\t\t'.join([str(exp) for exp in self.classes])
            )

    def pprint(self):
        CP = self.constant_pool
        print "I am: ", CP[CP[self.this_package].name_index], " with version ", CP[self.this_package].version, " and AID ", a2s(CP[self.this_package].aid)
        print "I export ", len(self.classes), " classes (including interfaces). Those are:"
        for cls in self.classes:
            print " - ", CP[CP[cls.name_index].name_index], "TK:", cls.token
            print "\tinherits from ",cls.export_supers_count, "classes, those are:"
            for sp in cls.supers:
                print "\t - ", CP[CP[sp].name_index]
            if cls.export_interfaces_count:
                print "\timplements the following ", cls.export_interfaces_count, "interfaces:"
                for int in cls.interfaces:
                    print "\t - ", CP[CP[int].name_index]
            if cls.export_fields_count:
                print "\thas the following ", cls.export_fields_count, "fields:"
                for fld in cls.fields:
                    assert len(fld.attributes) == 1
                    print "\t - ", CP[fld.name_index], "of type", CP[fld.descriptor_index], "TK:", fld.token, "(",CP[fld.attributes[0].constant_value_index], ")"
            if cls.export_methods_count:
                print "\thas the following", cls.export_methods_count, "methods:"
                for mtd in cls.methods:
                    print "\t - ", CP[mtd.name_index], "TK:", mtd.token, "(", CP[mtd.descriptor_index], ")"

    @property
    def AID(self):
        return self.constant_pool[self.this_package].aid

    def collectrefs(self):
        CP = self.constant_pool
        refs = {}
        for cls in self.classes:
            tmp = {}
            clsname = str(CP[CP[cls.name_index].name_index])
            clsname = clsname.replace('/','.')
            refs[clsname] = (cls.token, )
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
        return refs

def process(exp, options):
    if options.pretty_print:
        exp.pprint()
    return exp.AID, exp.collectrefs()

def main():
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
