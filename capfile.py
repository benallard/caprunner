import zipfile

from utils import *

class PackageInfo(object):
    def __init__(self, data):
        self.data = data
        self.minor_version = u1(self.data[:1])
        self.major_version = u1(self.data[1:2])
        self.aid_length = u1(self.data[2:3])
        self.aid = u1a(self.aid_length, self.data[3:])
        self.size = self.aid_length + 3

    @property
    def version(self):
        return (self.major_version, self.minor_version)

    def __str__(self):
        return "AID: %s %s" % (a2s(self.aid), self.version)

class Component(object):
    def __init__(self, data, version=None):
        self.data = data
        if version is not None:
            self.version = version
        self.tag = u1(self.data[:1])
        self.size = u2(self.data[1:3])
        self.info = u1a(self.size, self.data[3:])

    def __str__(self):
        return "< Component:\n\tTag:%d\n\tSize:%d\nInfo: %s\n>" % (
            self.tag,
            self.size,
            a2s(self.info)
            )

class Header(Component):

    class PackageName(object):
        def __init__(self, data):
            self.data = data
            self.name_length = u1(data[:1])
            self.name = u1a(name_length, data[1:])
        def __str__(self):
            return ''.join([chr(c) for c in self.name])

    def __init__(self, data):
        Component.__init__(self, data)
        self.magic = u4(self.data[3:7])
        self.minor_version = u1(self.data[7:8])
        self.major_version = u1(self.data[8:9])
        self.flags = u1(self.data[9:10])
        self.package = PackageInfo(self.data[10:])
        if self.version >= (2,2):
            shift = 13 + self.package.aid_length
            self.package_name = self.PackageName(self.data[shift:])

    @property
    def version(self):
        return (self.major_version, self.minor_version)

    def __str__(self):
        return "< Header:\n\tMagic: %08X\n\tVersion: %s\n\t%s\n>" % (
            self.magic,
            self.version,
            self.package
            )

class Directory(Component):

    class StaticFieldSizeInfo(object):
        def __init__(self, data):
            self.data = data
            self.image_size = u2(data[:2])
            self.array_init_count = u2(data[2:4])
            self.array_init_size = u2(data[4:6])
        def __str__(self):
            return "Image size: %d, Array_init_count: %d, Array_init_size: %d" % (
                self.image_size,
                self.array_init_count,
                self.array_init_size
                )

    class CustomComponentInfo(object):
        def __init__(self, data):
            self.data = data
            self.component_tag = u1(data[:1])
            self.size = u2(data[1:2])
            self.aid_length = u1(data[3:4])
            self.aid = u1a(aid_length, data[4:])

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.num_components = {(2,1): 11, (2,2): 12}[self.version]
        self.component_sizes = u2a(self.num_components, self.data[3:])
        self.static_field_size = self.StaticFieldSizeInfo(
            self.data[self.num_components*2+3:])
        self.import_count = u1(self.data[self.num_components*2+9:])
        self.applet_count = u1(self.data[self.num_components*2+10:])
        self.custom_count = u1(self.data[self.num_components*2+11:])
        self.custom_components = []
        shift = self.num_components*2+12
        for i in xrange(self.custom_count):
            data = self.data[shift:]
            cstm = self.CustomComponentInfo(data)
            self.custom_components.append(cstm)
            shift += cstm.aid_length + 4

    def __str__(self):
        return "< Directory:\n\tSizes: %s\n\tStatic: %s\n\tImports: %d\n\tApplets: %d\n\tCustoms: %s\n>" % (
            self.component_sizes,
            self.static_field_size,
            self.import_count,
            self.applet_count,
            self.custom_components
            )

class Applet(Component):

    class AppletInfo(object):
        def __init__(self, data):
            self.aid_length = u1(data[:1])
            self.aid = u1a(self.aid_length, data[1:])
            self.install_method_offset = u2(data[self.aid_length+1:])
        def __str__(self):
            return "AID: %s, Install_Offset: %d" % (
                a2s(self.aid),
                self.install_method_offset)

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.count = u1(self.data[3:4])
        self.applets = []
        shift = 4
        for i in xrange(self.count):
            data = self.data[shift:]
            app = self.AppletInfo(data)
            self.applets.append(app)
            shift += app.aid_length + 3

    def __str__(self):
        return "< Applet:\n\t%s\n>" % '\n\t'.join([str(applet) for applet in self.applets])

class Import(Component):
    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.count = u1(self.data[3:4])
        self.packages = []
        shift = 4
        for i in xrange(self.count):
            pkg_info = PackageInfo(self.data[shift:])
            self.packages.append(pkg_info)
            shift += pkg_info.size

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

class ConstantPool(Component):
    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.count = u2(self.data[3:5])
        self.constant_pool = []
        shift = 5
        for i in xrange(self.count):
            cp_info = CPInfo.get(self.data[shift:])
            self.constant_pool.append(cp_info)
            shift += cp_info.size

    def __str__(self):
        return "< ConstantPool: \n\t%s\n>" % '\n\t'.join([str(cp_info) for cp_info in self.constant_pool])

class CAPFile(object):
    def __init__(self, path):
        self.path = path
        self.zipfile = zipfile.ZipFile(self.path, 'r')
        self.Header = Header(self.zipfile.read(self._getFileName('Header')))
        self.Directory = Directory(self.zipfile.read(self._getFileName('Directory')), self.version)
        self.Applet = Applet(self.zipfile.read(self._getFileName('Applet')), self.version)
        self.Import = Import(self.zipfile.read(self._getFileName('Import')), self.version)
        self.ConstantPool = ConstantPool(self.zipfile.read(self._getFileName('ConstantPool')), self.version)

    @property
    def version(self):
        return self.Header.version

    def _getFileName(self, component):
        for name in self.zipfile.namelist():
            if component in name:
                return name

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
