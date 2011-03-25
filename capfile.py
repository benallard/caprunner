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
    COMPONENT_Header = 1
    COMPONENT_Directory = 2
    COMPONENT_Applet = 3
    COMPONENT_Import = 4
    COMPONENT_ConstantPool = 5
    COMPONENT_Class = 6
    COMPONENT_Method = 7
    COMPONENT_StaticField = 8
    COMPONENT_ReferenceLocation = 9
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
    size = 2
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

class Class(Component):

    class TypeDescriptor(object):
        def __init__(self, data):
            self.nibble_count = u1(data[:1])
            self.type = u1a((self.nibble_count+1)/2, data[1:])
            self.size = 1 + (self.nibble_count+1)/2

        def getTypeNib(self, i):
            if i % 2 == 0:
                return self.type[i / 2] & 0xF0 >> 4
            else:
                return self.type[i/2] & 0x0F

        def __str__(self):
            "That one can be pretty funny"
            typeDescr = {1: "void", 2:"boolean", 3: "byte", 4: "short", 5: "int", 6: "ref", 10: "array of bool", 11: "array of byte", 12: "array of short", 13: "array of int", 14: "array of ref"}
            res = []
            i = 0
            while i < self.nibble_count:
                nibble = self.getTypeNib(i)
                res += typeDescr[nibble]
                if nibble in [6, 14]:
                    p = self.getTypeNib(i+1) << 4 + self.getTypeNib(i+2)
                    c = self.getTypeNib(i+3) << 4 + self.getTypeNib(i+4)
                    res += "%d.%d" % (p, c)
                    i += 4
            return ' '.join(res)

    class BaseInfo(object):
        ACC_INTERFACE = 0x8
        ACC_SHAREABLE = 0x4
        ACC_REMOTE = 0x2
        def __init__(self, data):
            self.data = data
            bitfield = u1(self.data[:1])
            self.flags = (bitfield & 0xF0) >> 4
            self.isInterface = bool(self.flags & self.ACC_INTERFACE)
            self.isShareable = bool(self.flags & self.ACC_SHAREABLE)
            self.isRemote = bool(self.flags & self.ACC_REMOTE)
            self.interface_count = bitfield & 0x0F

        @classmethod
        def isInterface(cls, bitfield):
            flags = (bitfield & 0xF0) >> 4
            return flags & cls.ACC_INTERFACE == cls.ACC_INTERFACE

    class InterfaceInfo(BaseInfo):

        class InterfaceNameInfo(object):
            def __init__(self, data):
                self.interface_name_length = u1(data[:1])
                self.interface_name = u1a(self.interface_name_length, data[1:])
            def __str__(self):
                return ''.join([chr(c) for c in self.interface_name])

        def __init__(self, data):
            Class.BaseInfo.__init__(self, data)
            self.superinterfaces = []
            shift = 1
            for i in xrange(self.interface_count):
                self.superinterfaces.append(Classref(self.data[shift:]))
                shift += Classref.size
            if self.isRemote:
                # and only starting from (2, 2)
                self.interface_name = self.InterfaceNameInfo(data[shift:])
                shift += self.interface_name.interface_name_length + 1
            self.size = shift
        def __str__(self):
            return "InterfaceInfo: Super: %s %s" % (
                ', '.join(self.superinterfaces),
                self.isRemote and self.interface or ""
                )
                

    class ClassInfo(BaseInfo):

        class ImplementedInterfaceInfo(object):
            def __init__(self, data):
                self.interface = Classref(data[:2])
                self.count = u1(data[2:3])
                self.index = u1a(self.count, data[3:])
                self.size =  self.count + 3

        class RemoteInterfaceInfo(object):

            class RemoteMethodInfo(object):
                size = 5
                def __init__(self, data):
                    self.remote_method_hash = u2(data[:2])
                    self.signature_offset = u2(data[:2])
                    self.virtual_method_token = u1(data[:1])
                def __str__(self):
                    return "RemoteHash: %d, SigOffset: %d, VirtMethTok: %d" % (
                        self.remote_method_hash,
                        self.signature_offset,
                        self.virtual_method_token
                        )

            def __init__(self, data):
                self.remote_method_count = u1(data[:1])
                self.remote_methods = []
                shift = 1
                for i in xrange(self.remote_methode_count):
                    self.remote_methods.append(self.RemoteMethodInfo(data[shift:]))
                    shift += self.RemoteMethodInfo.size
                self.hash_modifier_length = u1(data[shift:])
                self.hash_modifier = u1a(self.hash_modifier_length, data[shift+1:])
                shift += self.hash_modifier_length + 1
                self.class_name_length = u1(data[shift:])
                self.class_name = u1a(self.class_name_length, data[shift+1:])
                shift += self.class_name_length + 1
                self.remote_interfaces_count = u1(data[shift:])
                self.remote_interfaces = []
                shift += 1
                for i in xrange(self.remote_interfaces_count):
                    self.remote_interfaces.append(Classref(data[shift:]))
                    shift += Classref.size
                self.size = shift
            def __str__(self):
                return "RemoteInterfaceInfo %s: %d methods, %d interfaces" % (
                    ''.join([chr(c) for c in self.class_name]),
                    self.remote_method_count,
                    self.remote_interfaces_count
                    )

        def __init__(self, data):
            Class.BaseInfo.__init__(self, data)
            self.super_class_ref = Classref(data[1:3])
            self.declared_instance_size = u1(data[3:4])
            self.first_reference_token = u1(data[4:5])
            self.reference_count = u1(data[5:6])
            self.public_method_table_base = u1(data[6:7])
            self.public_method_table_count = u1(data[7:8])
            self.package_method_table_base = u1(data[8:9])
            self.package_method_table_count = u1(data[9:10])
            shift = 10
            self.public_virtual_method_table = u2a(self.public_method_table_count, data[shift:])
            shift += self.public_method_table_count*2
            self.package_virtual_method_table = u2a(self.package_method_table_count, data[shift:])
            shift += self.package_method_table_count*2
            self.interfaces = []
            for i in xrange(self.interface_count):
                cls = self.ImplementedInterfaceInfo(data[shift:])
                self.interfaces.append(cls)
                shift += cls.size
            if self.flags & self.ACC_REMOTE == self.ACC_REMOTE:
                self.remote_interface = self.RemoteInterfaceInfo(data[shift:])
                shift += self.remote_interface.size
            self.size = shift
        def __str__(self):
            return "ClassInfo: super: %s %d public methods, %d package methods" % (
                self.super_class_ref,
                self.public_method_table_count,
                self.package_method_table_count
                )

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        shift = 3
        if self.version >= (2, 2):
            self.signature_pool_length = u2(self.data[3:5])
            shift += 2
            self.signature_pool = []
            for i in xrange(signature_pool_length):
                typ_descr = self.TypeDescriptor(self.data[shift:])
                self.signature_pool.append(typ_descr)
                shift += typ_descr.size
        self.interfaces = []
        self.classes = []
        # this is actually weird that we don't know beforehand how much class there will be
        while shift < self.size:
            data = self.data[shift:]
            if self.BaseInfo.isInterface(u1(self.data[shift:])):
                cls = self.InterfaceInfo(data)
                self.interfaces.append(cls)
                shift += cls.size
            else:
                cls = self.ClassInfo(data)
                self.classes.append(cls)
                shift += cls.size

    def __str__(self):
        return "< Class:\n\tInterfaces:\n\t\t%s\n\tClasses:\n\t\t%s\n>" % (
            '\n\t\t'.join([str(int) for int in self.interfaces]),
            '\n\t\t'.join([str(cls) for cls in self.classes])
            )

class CAPFile(object):
    def __init__(self, path):
        self.path = path
        self.zipfile = zipfile.ZipFile(self.path, 'r')
        self.Header = Header(self.zipfile.read(self._getFileName('Header')))
        self.Directory = Directory(self.zipfile.read(self._getFileName('Directory')), self.version)
        if self.Directory.component_sizes[Component.COMPONENT_Applet - 1] != 0:
            # Applet is optionnal
            self.Applet = Applet(self.zipfile.read(self._getFileName('Applet')), self.version)
        else:
            self.Applet = None
        self.Import = Import(self.zipfile.read(self._getFileName('Import')), self.version)
        self.ConstantPool = ConstantPool(self.zipfile.read(self._getFileName('ConstantPool')), self.version)
        self.Class = Class(self.zipfile.read(self._getFileName('Class')), self.version)

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
    if cap.Applet is not None:
        print Component(cap.Applet.data)
        print cap.Applet
    print cap.Import
    print cap.ConstantPool
    print cap.Class
