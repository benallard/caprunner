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

        class FieldInfo(object):

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
            def __init__(self, data):
                self.data = data
                self.token = u1(self.data[:1])
                self.access_flags = u2(self.data[1:3])
                self.name_index = u2(self.data[3:5])
                self.descriptor_index = u2(self.data[5:7])

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
            return "ClassInfo: name @%d, %d supers, %d interfaces, %d fields, %d methods" % (
                self.name_index,
                self.export_supers_count,
                self.export_interfaces_count,
                self.export_fields_count,
                self.export_methods_count)

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

if __name__ == "__main__":
    import sys
    f = open(sys.argv[1])
    exp = ExportFile(f.read())
    print exp
    exp.pprint()
