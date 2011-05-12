import zipfile

from utils import *
from bytecode import disassemble

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
    COMPONENT_Export = 10
    COMPONENT_Descriptor = 11
    COMPONENT_Debug = 12
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
    size = 4
    def __init__(self, data):
        self.data = data
        self.tag = u1(data[:1])
        self.info = u1a(3, data[1:4])
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
            self.package_token = u1(data[:1]) & 0x7F
            self.class_token = u1(data[1:2])
        def __str__(self):
            return "Ext: pkg: %d, cls: %d" % (self.package_token, self.class_token)
    def __init__(self, data):
        self.internal_class_ref = u2(data[:2])
        self.external_class_ref = self.Externalref(data[:2])
        self.isExternal = bool(u1(data[:1]) & 0x80)
        if self.isExternal:
            self.class_ref = self.external_class_ref
        else:
            self.class_ref = self.internal_class_ref
    def __str__(self):
        if not self.isExternal:
            return "Int: cls@%d" % self.class_ref
        else:
            return "%s" % self.class_ref

class CPInfoClassref(CPInfo, Classref):
    def __init__(self, data):
        CPInfo.__init__(self, data)
        Classref.__init__(self, data[1:])
        self.padding = u1(data[3:4])
    def __str__(self):
        return "<CPInfoClassRef %s>" % Classref.__str__(self)

class ClassTokenref(Classref):
    def __init__(self, data):
        Classref.__init__(self, data)
        self.token = u1(data[2:3])
    def __str__(self):
        return "%s, token %d" % (Classref.__str__(self), self.token)

class CPInfoClassTokenref(CPInfo, ClassTokenref):
    def __init__(self, data):
        CPInfo.__init__(self, data)
        ClassTokenref.__init__(self, data[1:])
    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, ClassTokenref.__str__(self))

class CPInfoInstanceFieldref(CPInfoClassTokenref): pass
class CPInfoVirtualMethodref(CPInfoClassTokenref):
    def __init__(self, data):
        CPInfoClassTokenref.__init__(self, data)
        self.isPrivate = bool(self.token & 0x80)
        self.token &= 0x7f
class CPInfoSuperMethodref(CPInfoVirtualMethodref): pass

class StaticBaseref(object):
    size = 3
    class Internalref(object):
        def __init__(self, data):
            self.padding = u1(data[:1])
            self.offset = u2(data[1:3])
        def __str__(self):
            return "Int: %d" % (self.offset)

    class Externalref(object):
        def __init__(self, data):
            self.package_token = u1(data[:1]) & 0x7F
            self.class_token = u1(data[1:2])
            self.token = u1(data[2:3])
        def __str__(self):
            return "Ext: pkg: %d, cls: %d, token: %d" % (self.package_token, self.class_token, self.token)

    def __init__(self, data):
        self.internal_ref = self.Internalref(data)
        self.external_ref = self.Externalref(data)
        self.isExternal = bool(u1(data[:1]) & 0x80)
        if self.isExternal:
            self._ref = self.external_ref
        else:
            self._ref = self.internal_ref
    def __str__(self):
        return "%s" % self._ref

class CPInfoStaticBaseref(CPInfo, StaticBaseref):
    def __init__(self, data):
        CPInfo.__init__(self, data)
        StaticBaseref.__init__(self, data[1:])
    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, StaticBaseref.__str__(self))

class CPInfoStaticFieldref(CPInfoStaticBaseref):
    def __init__(self, data):
        CPInfoStaticBaseref.__init__(self, data)
        self.static_field_ref = self._ref

class CPInfoStaticMethodref(CPInfoStaticBaseref):
    """
    Static method references include references to static methods, 
    constructors, and private virtual methods.
    """
    def __init__(self, data):
        CPInfoStaticBaseref.__init__(self, data)
        self.static_method_ref = self._ref

class ConstantPool(Component):
    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.count = u2(self.data[3:5])
        self.constant_pool = []
        shift = 5
        for i in xrange(self.count):
            cp_info = CPInfo.get(self.data[shift:])
            self.constant_pool.append(cp_info)
            shift += CPInfo.size

    def __str__(self):
        return "< ConstantPool: \n\t%s\n>" % '\n\t'.join(
            ["%d: %s" % (i, str(self.constant_pool[i])) for i in xrange(self.count)])

class TypeDescriptor(object):
    def __init__(self, data):
        self.nibble_count = u1(data[:1])
        self.type = u1a((self.nibble_count+1)/2, data[1:])
        self.size = 1 + (self.nibble_count+1)/2

    def getTypeNib(self, i):
        if i % 2 == 0:
            return (self.type[i / 2] & 0xF0) >> 4
        else:
            return self.type[i / 2] & 0x0F

    def __str__(self):
        "That one can be pretty funny"
        typeDescr = {1: "void", 2:"boolean", 3: "byte", 4: "short", 5: "int", 6: "ref", 10: "array of bool", 11: "array of byte", 12: "array of short", 13: "array of int", 14: "array of ref"}
        res = []
        i = 0
        while i < self.nibble_count:
            nibble = self.getTypeNib(i)
            res.append(typeDescr[nibble])
            i += 1
            if nibble in [6, 14]:
                p = (self.getTypeNib(i) << 4 + self.getTypeNib(i+1)) & 0x7F
                c = self.getTypeNib(i+2) << 4 + self.getTypeNib(i+3)
                res.append("%d.%d" % (p, c))
                i += 4
        return ' '.join(res)

class Class(Component):

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
                ', '.join([str(int) for int in self.superinterfaces]),
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
                typ_descr = TypeDescriptor(self.data[shift:])
                self.signature_pool.append(typ_descr)
                shift += typ_descr.size
        self.interfaces = {}
        self.classes = {}
        # this is actually weird that we don't know beforehand how much class there will be
        while shift < self.size:
            data = self.data[shift:]
            if self.BaseInfo.isInterface(u1(self.data[shift:])):
                cls = self.InterfaceInfo(data)
                self.interfaces[shift - 3] = cls # -3: info block, not data
                shift += cls.size
            else:
                cls = self.ClassInfo(data)
                self.classes[shift - 3] = cls # -3: idem
                shift += cls.size

    def __str__(self):
        return "< Class:\n\tInterfaces:\n\t\t%s\n\tClasses:\n\t\t%s\n>" % (
            '\n\t\t'.join(["%d: %s" % (idx, int) for (idx, int) in self.interfaces.iteritems()]),
            '\n\t\t'.join(["%d: %s" % (idx, cls) for (idx, cls) in self.classes.iteritems()])
            )

class Method(Component):

    class ExceptionHandlerInfo(object):
        size = 8
        def __init__(self, data):
            self.start_offset = u2(data[:2])
            bitfield = u2(data[2:4])
            self.stop_bit = bool(bitfield & 0x8000)
            self.active_length = bitfield & 0x07FF
            self.handler_offset = u2(data[4:6])
            self.catch_type_index = u2(data[6:8])
        def __str__(self):
            return "range: [%d:+%d] handler: %d%s, catch @ %d" % (
                self.start_offset, 
                self.active_length, 
                self.handler_offset,
                self.stop_bit and " STOP" or "",
                self.catch_type_index
                )
    
    class MethodInfo(object):

        class BaseHeaderInfo(object):
            ACC_EXTENDED = 0x8
            ACC_ABSTRACT = 0x4
            def __init__(self, data):
                bitfield = u1(data[:1])
                self.flags = (bitfield & 0xF0) >> 4
                self.isExtended = bool(self.flags & self.ACC_EXTENDED)
                self.isAbstract = bool(self.flags & self.ACC_ABSTRACT)
            @classmethod
            def isExtended(cls, bitfield):
                flags = (bitfield & 0xF0) >> 4
                return bool(flags & cls.ACC_EXTENDED)
                
        class MethodHeaderInfo(BaseHeaderInfo):
            size = 2
            def __init__(self, data):
                Method.MethodInfo.BaseHeaderInfo.__init__(self, data)
                bitfield = u1(data[:1])
                self.max_stack = bitfield & 0x0F
                bitfield = u1(data[1:2])
                self.nargs = (bitfield & 0xF0) >> 4
                self.max_locals = bitfield & 0x0F
            def __str__(self):
                return "Mtdinfo: %d max stack, %d nargs, %d max locals" % (
                    self.max_stack,
                    self.nargs,
                    self.max_locals
                    )

        class ExtendedMethodHeaderInfo(BaseHeaderInfo):
            size = 4
            def __init__(self, data):
                Method.MethodInfo.BaseHeaderInfo.__init__(self, data)
                self.max_stack = u1(data[1:2])
                self.nargs = u1(data[2:3])
                self.max_locals = u1(data[3:4])
            def __str__(self):
                return "Mtdinfo: %d max stack, %d nargs, %d max locals" % (
                    self.max_stack,
                    self.nargs,
                    self.max_locals
                    )

        def __init__(self, data, bytecodelen):
            self.method_info = {
                False: self.MethodHeaderInfo, 
                True: self.ExtendedMethodHeaderInfo
                }[self.BaseHeaderInfo.isExtended(u1(data[:1]))](data)
            self.size = self.method_info.size
            if not self.method_info.isAbstract:
                self.bytecodes = u1a(bytecodelen, data[self.method_info.size:])
                self.size += bytecodelen
        def __str__(self):
            return "Methode: %s, (%s)" % (
                self.method_info,
                not self.method_info.isAbstract and ', '.join(disassemble(self.bytecodes)) or ""
                )

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.handler_count = u1(self.data[3:4])
        shift = 4
        self.exception_handlers = []
        for i in xrange(self.handler_count):
            self.exception_handlers.append(self.ExceptionHandlerInfo(self.data[shift:]))
            shift += self.ExceptionHandlerInfo.size
        self.methods = {}
        # Quite weird we don't know beforehand how much methods we'll get ...
        # So we need to postpone the initialisation of that array

    def __str__(self):
        return "< Method:\n\tExceptionHandlers:\n\t\t%s\n\tMethods:\n\t\t%s\n>" %(
            '\n\t\t'.join([str(excp) for excp in self.exception_handlers]),
            '\n\t\t'.join(["%d: %s" % (idx, mtd) for (idx, mtd) in self.methods.iteritems()])
            )

class StaticField(Component):

    class ArrayInitInfo(object):
        type_boolean = 2
        type_byte = 3
        type_short = 4
        type_int = 5
        def __init__(self, data):
            self.type = u1(data[:1])
            self.count = u2(data[1:3])
            self.values = u1a(self.count, data[3:])
            self.size = self.count + 3
        def __str__(self):
            return "%s [] = %s" % (
                {2: "boolean", 3: "byte", 4: "short", 5: "int"}[self.type],
                a2s(self.values))

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.image_size = u2(self.data[3:5])
        self.reference_count = u2(self.data[5:7])
        self.array_init_count = u2(self.data[7:9])
        shift = 9
        self.array_init = []
        for i in xrange(self.array_init_count):
            aii = self.ArrayInitInfo(self.data[shift:])
            self.array_init.append(aii)
            shift += aii.size
        self.default_value_count = u2(self.data[shift:])
        self.non_default_value_count = u2(self.data[shift+2:])
        self.non_default_values = u1a(self.non_default_value_count, self.data[shift+4:])
    def __str__(self):
        return "< StaticField:\n\tImage size: %d\n\tRef Count: %d\n\tArray Init: (%d)\n\t\t%s\n\tDefault values: %d\n\tNon default Values: (%d) %s\n>" % (
            self.image_size,
            self.reference_count,
            self.array_init_count,
            '\n\t\t'.join([str(aii) for aii in self.array_init]),
            self.default_value_count,
            self.non_default_value_count,
            a2s(self.non_default_values)
            )

class RefLocation(Component):
    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.byte_index_count = u2(data[3:5])
        self.offsets_to_byte_indices = u1a(self.byte_index_count, self.data[5:])
        shift = self.byte_index_count + 5
        self.byte2_index_count = u2(data[shift:])
        self.offsets_to_byte2_indices = u1a(self.byte2_index_count, self.data[shift+2:])
        shift += self.byte2_index_count + 2
    def offsets(self, a):
        offs = 0
        for v in a:
            offs += v
            if v != 0xff:
                yield offs
    def __str__(self):
        return "< RefLocation:\n\t%s\n\t%s\n>" % (
            ', '.join([str(offs) for offs in self.offsets(self.offsets_to_byte_indices)]),
            ', '.join([str(offs) for offs in self.offsets(self.offsets_to_byte2_indices)])
            )

class Export(Component):

    class ClassExportInfo(object):
        def __init__(self, data):
            self.class_offset = u2(data[:2])
            self.static_field_count = u1(data[2:3])
            self.static_method_count = u1(data[3:4])
            shift = 4
            self.static_field_offsets = u2a(self.static_field_count, data[shift:])
            shift += self.static_field_count * 2
            self.static_method_offsets = u2a(self.static_method_count, data[shift:])
            self.size = shift + self.static_method_count * 2
        def __str__(self):
            return "Class @%d, static fields @ %s, static methods @ %s" % (
                self.class_offset,
                ', '.join([str(offs) for offs in self.static_field_offsets]),
                ', '.join([str(offs) for offs in self.static_method_offsets])
                )
    
    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.class_count = u1(self.data[3:4])
        shift = 4
        self.class_exports = []
        for i in xrange(self.class_count):
            clsexp = self.ClassExportInfo(self.data[shift:])
            self.class_exports.append(clsexp)
            shift += clsexp.size
    def __str__(self):
        return "< Export:\n\t - %s\n>" % (
            '\n\t - '.join([str(clsexp) for clsexp in self.class_exports]))

class Descriptor(Component):

    class ClassDescriptorInfo(object):
        ACC_PUBLIC = 0x01
        ACC_FINAL = 0x10
        ACC_INTERFACE = 0x40
        ACC_ABSTRACT = 0x80
        class FieldDescriptorInfo(object):
            size = 7
            ACC_PUBLIC = 0x01
            ACC_PRIVATE = 0x02
            ACC_PROTECTED = 0x04
            ACC_STATIC = 0x08
            ACC_FINAL = 0x10
            def __init__(self, data):
                self.token = u1(data[:1])
                self.access_flags = u1(data[1:2])
                self.isStatic = bool(self.access_flags & self.ACC_STATIC)
                self.static_field = StaticBaseref(data[2:])
                self.instance_field = ClassTokenref(data[2:])
                if self.isStatic:
                    self.field = self.static_field
                else:
                    self.field = self.instance_field
                shift = 5
                type = u2(data[shift:])
                self.primitive_type = type & 0x000F
                self.reference_type = type & 0x7FFF
                if bool(type & 0x8000):
                    self.type = self.primitive_type
                else:
                    self.type = self.reference_type
            def __str__(self):
                return "Field: %s%s of type %d" % (
                    self.isStatic and "STATIC " or "", self.field, self.type)

        class MethodDescriptorInfo(object):
            size = 12
            ACC_PUBLIC = 0x01
            ACC_PRIVATE = 0x02
            ACC_PROTECTED = 0x04
            ACC_STATIC = 0x08
            ACC_FINAL = 0x10
            ACC_ABSTRACT = 0x40
            ACC_INIT = 0x80
            def __init__(self, data):
                self.token = u1(data[:1])
                self.isPrivate = bool(self.token & 0x80)
                self.token &= 0x7f
                self.access_flags = u1(data[1:2])
                self.isConstructor = bool(
                    self.access_flags &
                    Descriptor.ClassDescriptorInfo.MethodDescriptorInfo.ACC_INIT)
                self.method_offset = u2(data[2:4])
                self.type_offset = u2(data[4:6])
                self.bytecode_count = u2(data[6:8])
                self.exception_handler_count = u2(data[8:10])
                self.exception_handler_index = u2(data[10:12])
            def __str__(self):
                return "Method: %d [%d:+%d],type: @%d excpt: %d @%d" % (
                    self.token,
                    self.method_offset,
                    self.bytecode_count,
                    self.type_offset,
                    self.exception_handler_count,
                    self.exception_handler_index
                    )

        def __init__(self, data):
            self.token = u1(data[:1])
            self.access_flags = u1(data[1:2])
            self.this_class_ref = Classref(data[2:])
            shift = Classref.size + 2
            self.interface_count = u1(data[shift:])
            self.field_count = u2(data[shift+1:])
            self.method_count = u2(data[shift+3:])
            shift += 5
            self.interfaces = []
            for i in xrange(self.interface_count):
                self.interfaces.append(Classref(data[shift:]))
                shift += Classref.size
            self.fields = []
            for i in xrange(self.field_count):
                fld = self.FieldDescriptorInfo(data[shift:])
                self.fields.append(fld)
                shift += fld.size
            self.methods = []
            for i in xrange(self.method_count):
                mtd = self.MethodDescriptorInfo(data[shift:])
                self.methods.append(mtd)
                shift += mtd.size
            self.size = shift
        def __str__(self):
            return "Class: %s, Interfaces: (%s), Fields: (%s), Methods: (%s)" % (
                self.this_class_ref,
                ', '.join([str(int) for int in self.interfaces]),
                ', '.join([str(int) for int in self.fields]),
                ', '.join([str(int) for int in self.methods]),
                )

    class TypeDescriptorInfo(object):
        def __init__(self, data, size):
            self.constant_pool_count = u2(data[:2])
            self.constant_pool_types = u2a(self.constant_pool_count, data[2:])
            shift = self.constant_pool_count * 2 + 2
            self.type_desc = {}
            while shift < size:
                type = TypeDescriptor(data[shift:])
                self.type_desc[shift] = type
                shift += type.size
            self.size = shift
        def __str__(self):
            return "TypeDescr: CstPool: (%s), types: (%s)" % (
                ', '.join([str(cst) for cst in self.constant_pool_types]),
                ', '.join(["%d: %s" % (idx, typ) for (idx, typ) in self.type_desc.iteritems()])
                )

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.class_count = u1(self.data[3:4])
        shift = 4
        self.classes = []
        for i in xrange(self.class_count):
            cls = self.ClassDescriptorInfo(data[shift:])
            self.classes.append(cls)
            shift += cls.size
        self.types = self.TypeDescriptorInfo(data[shift:], self.size - shift)
    def __str__(self):
        return "< Descriptor:\n\tClasses:\n\t\t - %s\n\tTypes: %s\n>" % (
            '\n\t\t - '.join([str(cls) for cls in self.classes]),
            self.types
            )

class Debug(Component):

    class Utf8Info(object):
        def __init__(self, data):
            self.length = u2(data[:2])
            self.bytes = u1a(self.length, data[2:])
            self.size = self.length + 2
        def __str__(self):
            return ''.join([chr(b) for b in self.bytes])

    class ClassDebugInfo(object):
        ACC_PUBLIC = 0x0001
        ACC_FINAL = 0x0010
        ACC_REMOTE = 0x0020
        ACC_INTERFACE = 0x0200
        ACC_ABSTRACT = 0x0400
        ACC_SHAREABLE = 0x0800
        class FieldDebugInfo(object):
            size = 10
            ACC_PUBLIC = 0x0001
            ACC_PRIVATE = 0x0002
            ACC_PROTECTED = 0x0004
            ACC_STATIC = 0x0008
            ACC_FINAL = 0x0010
            def __init__(self, data):
                self.name_index = u2(data[:2])
                self.descriptor_index = u2(data[2:4])
                self.access_flags = u2(data[4:6])
                self.token = u1(data[9:10])
                self.location = u2(data[8:10])
                self.constant_value = u4(data[6:10])
                if bool(self.access_flags & self.ACC_STATIC):
                    self.contents = self.location
                elif bool(self.access_flags & self.ACC_FINAL):
                    self.contents = self.constant_value
                else:
                    self.contents = self.token

        class MethodDebugInfo(object):
            ACC_PUBLIC = 0x0001
            ACC_PRIVATE = 0x0002
            ACC_PROTECTED = 0x0004
            ACC_STATIC = 0x0008
            ACC_FINAL = 0x0010
            ACC_NATIVE = 0x0100
            ACC_ABSTRACT = 0x0400
            class VariableInfo(object):
                size = 9
                def __init__(self, data):
                    self.index = u1(data[:1])
                    self.name_index = u2(data[1:3])
                    self.descriptor_index = u2(data[3:5])
                    self.start_pc = u2(data[5:7])
                    self.length = u2(data[7:9])

            class LineInfo(object):
                size = 6
                def __init__(self, data):
                    self.start_pc = u2(data[:2])
                    self.end_pc = u2(data[2:4])
                    self.source_line = u2(data[4:6])

            def __init__(self, data):
                self.name_index = u2(data[:2])
                self.descriptor_index = u2(data[2:4])
                self.access_flags = u2(data[4:6])
                self.location = u2(data[6:8])
                self.header_size = u1(data[8:9])
                self.body_size = u2(data[9:11])
                self.variable_count = u2(data[11:13])
                self.line_count = u2(data[13:15])
                shift = 15
                self.variable_table = []
                for i in xrange(self.variable_count):
                    self.variable_table.append(self.VariableInfo(data[shift:]))
                    shift += self.VariableInfo.size
                self.line_table = []
                for i in xrange(self.line_count):
                    self.line_table.append(self.LineInfo(data[shift:]))
                    shift += self.LineInfo.size

        def __init__(self, data):
            self.name_index = u2(data[:2])
            self.access_flags = u2(data[2:4])
            self.location = u2(data[4:6])
            self.superclass_name_index = u2(data[6:8])
            self.source_file_index = u2(data[8:10])
            self.interface_count = u1(data[10:11])
            self.field_count = u2(data[11:13])
            self.method_count = u2(data[13:15])
            self.interface_name_indexes = u2a(self.interface_count, data[15:])
            shift = 15 + self.interface_count * 2
            self.fields = []
            for i in xrange(self.field_count):
                fld = self.FieldDebugInfo(data[shift:])
                self.fields.append(fld)
                shift += fld.size
            self.methods = []
            for i in xrange(self.method_count):
                mtd = self.MethodDebugInfo(data[shift:])
                self.methods.append(mtd)
                shift += mtd.size

    def __init__(self, data, version):
        Component.__init__(self, data, version)
        self.string_count = u2(self.data[3:5])
        shift = 5
        self.strings_table = []
        for i in xrange(self.string_count):
            string = self.Utf8Info(self.data[shift:])
            self.strings_table.append(string)
            shift += string.size
        self.package_name_index = u2(data[shift:])
        self.class_count = u2(data[shift + 2:])
        shift += 4
        self.classes = []
        for i in xrange(self.class_count):
            cls = self.ClassDebugInfo(data[shift:])
            self.classes.append(cls)
            shift += cls.size

class CAPFile(object):
    def __init__(self, path):
        self.path = path
        self.zipfile = zipfile.ZipFile(self.path, 'r')
        getComp = lambda name: self.zipfile.read(self._getFileName(name))
        self.Header = Header(getComp('Header'))
        self.Directory = Directory(getComp('Directory'), self.version)
        if self.Directory.component_sizes[Component.COMPONENT_Applet - 1] != 0:
            # Applet is optionnal
            self.Applet = Applet(getComp('Applet'), self.version)
        else:
            self.Applet = None
        self.Import = Import(getComp('Import'), self.version)
        self.ConstantPool = ConstantPool(getComp('ConstantPool'), self.version)
        self.Class = Class(getComp('Class'), self.version)
        self.Method = Method(getComp('Method'), self.version)
        self.StaticField = StaticField(getComp('StaticField'), self.version)
        self.RefLocation = RefLocation(getComp('RefLocation'), self.version)
        if self.Directory.component_sizes[Component.COMPONENT_Export - 1] != 0:
            self.Export = Export(getComp('Export'), self.version)
        else:
            self.Export = None
        self.Descriptor = Descriptor(getComp('Descriptor'), self.version)
        if ((self.version > (2,1)) and
            (self.Directory.component_sizes[Component.COMPONENT_Debug - 1] != 0)):
            self.Debug = Debug(getComp('Debug'), self.version)
        else:
            self.Debug = None
        
        self.postInit()

    def postInit(self):
        # We need to fiil the methods here.
        data = self.Method.data[3:]
        for cls in self.Descriptor.classes:
            for mtd in cls.methods:
                if mtd.method_offset == 0:
                    continue
                method = Method.MethodInfo(data[mtd.method_offset:], mtd.bytecode_count)
                self.Method.methods[mtd.method_offset] = method
                

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
    print cap.Header
    print cap.Directory
    if cap.Applet is not None:
        print cap.Applet
    print cap.Import
    print cap.ConstantPool
    print cap.Class
    print cap.Method
    print cap.StaticField
    print cap.RefLocation
    if cap.Export is not None:
        print cap.Export
    print cap.Descriptor
    if cap.Debug is not None:
        print cap.Debug
