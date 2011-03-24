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
        def __init__(self, data):
            CPInfo.__init__(self, data)
            self.bytes = u4(data[1:5])
            self.size = 5

    class CPInfoClassref(CPInfo):
        def __init__(self, data):
            CPInfo.__init__(self, data)
            self.name_index = u2(data[1:3])
            self.size = 3
            
        def getName(self, pool):
            return str(pool[self.name_index])

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
        def __init__(self, data):
            self.size = len(data)

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
            cls = ClassInfo(data)
            self.classes.append(cls)
            shift += cls.size
            
    @property
    def version(self):
        return (self.major_version, self.minor_version)

    def __str__(self):
        return "<ExportFile:\n\tMagic: %08X\n\tVersion: %s\n\tCstPool:\n\t\t%s\n\tThis:%s\n\tExports:%s\n>" % (
            self.magic,
            self.version,
            '\n\t\t'.join([str(cp_info) for cp_info in self.constant_pool]),
            self.constant_pool[self.this_package],
            '\n\t\t'.join([str(exp) for exp in self.classes])
            )

if __name__ == "__main__":
    import sys
    f = open(sys.argv[1])
    exp = ExportFile(f.read())
    print exp
