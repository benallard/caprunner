import zipfile

from utils import *

class PackageInfo(object):
    def __init__(self, data):
        self.data = data

    @cached_property
    def minor_version(self):
        return u1(self.data[:1])

    @cached_property
    def major_version(self):
        return u1(self.data[1:2])

    @cached_property
    def version(self):
        return (self.major_version, self.minor_version)

    @cached_property
    def aid_length(self):
        return u1(self.data[2:3])

    @cached_property
    def aid(self):
        return u1a(self.aid_length, self.data[3:])

    @cached_property
    def size(self):
        return self.aid_length + 3

    def __str__(self):
        return "AID: %s %s" % (a2s(self.aid), self.version)

class Component(object):
    def __init__(self, data, version=None):
        self.data = data
        if version:
            self.version = version

    @cached_property
    def tag(self):
        return u1(self.data[:1])

    @cached_property
    def size(self):
        return u2(self.data[1:3])

    @cached_property
    def info(self):
        return self.data[3:3+self.size]

    def __str__(self):
        return "< Component:\n\tTag:%d\n\tSize:%d\nInfo: %s\n>" % (
            self.tag,
            self.size,
            stringify(self.info)
            )

class ComponentWithCountU1(Component):
    @cached_property
    def count(self):
        return u1(self.data[3:4])

class ComponentWithCountU2(Component):
    @cached_property
    def count(self):
        return u2(self.data[3:5])

class Header(Component):
    @cached_property
    def magic(self):
        return u4(self.data[3:7])

    @cached_property
    def minor_version(self):
        return u1(self.data[7:8])

    @cached_property
    def major_version(self):
        return u1(self.data[8:9])

    @cached_property
    def version(self):
        return (self.major_version, self.minor_version)

    @cached_property
    def flags(self):
        return u1(self.data[9:10])

    @cached_property
    def package(self):
        return PackageInfo(self.data[10:])

    @cached_property
    def package_name(self):
        if self.version >= (2, 2):
            data = self.data[self.package.aid_length+13:]
            name_length = u1(data[:1])
            return {'name_length': name_length,
                    'name': u1a(name_length, data[1:])
                    }
        else:
            return None

    def __str__(self):
        return "< Header:\n\tMagic: %08X\n\tVersion: %s\n\t%s\n>" % (
            self.magic,
            self.version,
            self.package
            )

class Directory(Component):

    @cached_property
    def num_components(self):
        if self.version == (2, 1):
            return 11
        elif self.version == (2,2):
            return 12

    @cached_property
    def component_sizes(self):
        return u2a(self.num_components, self.data[3:])

    @cached_property
    def static_field_size(self):
        data = self.data[self.num_components*2+3:]
        return {'image_size': u2(data[:2]),
                'array_init_count': u2(data[2:4]),
                'array_init_size': u2(data[4:6])
                }

    @cached_property
    def import_count(self):
        return u1(self.data[self.num_components*2+9:])

    @cached_property
    def applet_count(self):
        return u1(self.data[self.num_components*2+10:])

    @cached_property
    def custom_count(self):
        try:
            return u1(self.data[self.num_components*2+11:])
        except IndexError:
            return 0

    @cached_property
    def custom_components(self):
        res = []
        shift = self.num_components*2+12
        for i in xrange(self.custom_count):
            data = self.data[shift:]
            aid_length = u1(data[3:4])
            res.append({'component_tag': u1(data[:1]),
                        'size': u2(data[1:2]),
                        'aid_length': aid_length,
                        'aid': u1a(aid_length, data[4:])
                        }
                       )
            shift += aid_length + 4
        return res

    def __str__(self):
        return "< Directory:\n\tSizes: %s\n\tStatic: %s\n\tImports: %d\n\tApplets: %d\n\tCustoms: %s\n>" % (
            self.component_sizes,
            self.static_field_size,
            self.import_count,
            self.applet_count,
            self.custom_components
            )

class Applet(ComponentWithCountU1):
    @cached_property
    def applets(self):
        res = []
        shift = 4
        for i in xrange(self.count):
            data = self.data[shift:]
            aid_length = u1(data[:1])
            res.append({'aid_length': aid_length,
                        'aid': u1a(aid_length, data[1:]),
                        'install_method_offset': u2(data[aid_length+1:])
                        }
                       )
            shift += aid_length + 3
        return res

    def __str__(self):
        return "< Applet:\n%s\n>" % '\n'.join([
            "\tAID: %s\n\tInstall_Offset: %d" % (
                a2s(applet['aid']),
                applet['install_method_offset']) for applet in self.applets])

class Import(ComponentWithCountU1):
    @cached_property
    def packages(self):
        res = []
        shift = 4
        for i in xrange(self.count):
            pkg_info = PackageInfo(self.data[shift:])
            res.append(pkg_info)
            shift += pkg_info.size
        return res

    def __str__(self):
        return "< Import:\n\t%s\n>" % '\n\t'.join([str(pkg_info) for pkg_info in self.packages])

class CPInfo(object):
    def __init__(self, data):
        self.data = data
        self.tag = u1(data[:1])
        self.info = u1a(3, data[1:4])
        self.size = 4
    def __str__(self):
        return "%d (%s)" % (self.tag, a2s(self.info))

    @staticmethod
    def get(data):
        return {1: CPInfoClassref,
                2: CPInfoInstanceFieldref,
                3: CPInfoVirtualMethodref,
                4: CPInfoSuperMethodref,
                5: CPInfoStaticFieldref,
                6: CPInfoStaticMethodref}[u1(data[:1])](data)

class Classref(object):
    class Externalref(object):
        def __init__(self, data):
            self.package_token = u1(data[:1])
            self.class_token = u1(data[1:2])
        def __str__(self):
            return "pkg: %d, cls: %d" % (self.package_token, self.class_token)
    def __init__(self, data):
        self.internal_class_ref = u2(data[:2])
        self.external_class_ref = self.Externalref(data[:2])
    def __str__(self):
        return "%d / %s" % (self.internal_class_ref, self.external_class_ref)

class CPInfoClassref(CPInfo, Classref):
    def __init__(self, data):
        CPInfo.__init__(self, data)
        Classref.__init__(self, data[1:])
        self.padding = u1(data[3:4])
    def __str__(self):
        return "<CPInfoClassRef %s>" % Classref.__str__(self)

class CPInfoInstanceFieldref(CPInfo, Classref):
    def __init__(self, data):
        CPInfo.__init__(self, data)
        Classref.__init__(self, data[1:])
        self.token = u1(data[3:4])
    def __str__(self):
        return "<%s %s, token: %d>" % (self.__class__.__name__, Classref.__str__(self), self.token)

CPInfoVirtualMethodref = CPInfoInstanceFieldref
CPInfoSuperMethodref = CPInfoInstanceFieldref

class CPInfoStaticFieldref(CPInfo):

    class Internalref(object):
        def __init__(self, data):
            self.padding = u1(data[:1])
            self.offset = u2(data[1:3])
        def __str__(self):
            return "%d" % (self.offset)

    class Externalref(object):
        def __init__(self, data):
            self.package_token = u1(data[:1])
            self.class_token = u1(data[1:2])
            self.token = u1(data[2:3])
        def __str__(self):
            return "pkg: %d, cls: %d, token: %d" % (self.package_token, self.class_token, self.token)

    def __init__(self, data):
        CPInfo.__init__(self, data)
        self.internal_ref = self.Internalref(data[1:])
        self.external_ref = self.Externalref(data[1:])

    def __str__(self):
        return "<%s %s / %s>" % (self.__class__.__name__, self.internal_ref, self.external_ref)

CPInfoStaticMethodref = CPInfoStaticFieldref

class ConstantPool(ComponentWithCountU2):
    @cached_property
    def constant_pool(self):
        res = []
        shift = 5
        for i in xrange(self.count):
            cp_info = CPInfo.get(self.data[shift:])
            res.append(cp_info)
            shift += cp_info.size
        return res

    def __str__(self):
        return "< ConstantPool: \n\t%s\n>" % '\n\t'.join([str(cp_info) for cp_info in self.constant_pool])

class CAPFile(object):
    def __init__(self, path):
        self.path = path
        self.zipfile = zipfile.ZipFile(self.path, 'r')

    @cached_property
    def version(self):
        return self.Header.version

    def _getFileName(self, component):
        for name in self.zipfile.namelist():
            if component in name:
                return name

    @cached_property
    def Header(self):
        return Header(self.zipfile.read(self._getFileName('Header')))

    @cached_property
    def Directory(self):
        return Directory(self.zipfile.read(self._getFileName('Directory')), self.version)

    @cached_property
    def Applet(self):
        return Applet(self.zipfile.read(self._getFileName('Applet')), self.version)

    @cached_property
    def Import(self):
        return Import(self.zipfile.read(self._getFileName('Import')), self.version)

    @cached_property
    def ConstantPool(self):
        return ConstantPool(self.zipfile.read(self._getFileName('ConstantPool')), self.version)

if __name__ == "__main__":
    import sys
    cap = CAPFile(sys.argv[1])
    print cap.zipfile.namelist()
    print cap.Header
    print Component(cap.Directory.data)
    print cap.Directory
    print Component(cap.Applet.data)
    print cap.Applet
    print cap.Import
    print cap.ConstantPool
