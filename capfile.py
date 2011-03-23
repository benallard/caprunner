import zipfile

from classfile import u1, u2, u4

## {{{ http://code.activestate.com/recipes/576563/ (r1)
def cached_property(f):
    """returns a cached property that is calculated by function f"""
    def get(self):
        try:
            return self._property_cache[f]
        except AttributeError:
            self._property_cache = {}
            x = self._property_cache[f] = f(self)
            return x
        except KeyError:
            x = self._property_cache[f] = f(self)
            return x
        
    return property(get)
## end of http://code.activestate.com/recipes/576563/ }}}

def u1a(size, data):
    """ u1 array """
    return [u1(data[i:i+1]) for i in xrange(size)]

def u2a(size, data):
    """ u2 array """
    return [u2(data[i*2:i*2+2]) for i in xrange(size)]

def a2s(a):
    """ array to string """
    return ' '.join(["%02X" % i for i in a])

def stringify(s):
    return ' '.join(["%02X" % ord(c) for c in s])

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
    def package_info(self):
        return PackageInfo(self.data[10:])

    @cached_property
    def package_name_info(self):
        if self.version >= (2, 2):
            data = self.data[self.package_info.aid_length+13:]
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
            self.package_info
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
    def static_field_size_info(self):
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
    def custom_component_info(self):
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
            self.static_field_size_info,
            self.import_count,
            self.applet_count,
            self.custom_component_info
            )

class Applet(Component):
    @cached_property
    def count(self):
        return u1(self.data[3:4])

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

if __name__ == "__main__":
    import sys
    cap = CAPFile(sys.argv[1])
    print cap.zipfile.namelist()
    print cap.Header
    print Component(cap.Directory.data)
    print cap.Directory
    print Component(cap.Applet.data)
    print cap.Applet
