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

def stringify(s):
    return ' '.join(["%02X" % c for c in s])

class Component(object):
    def __init__(self, data):
        self.data = data

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
        return "< Component:\n\tTag:%d\n\tSize:%d\n>" % (self.tag, self.size)
        

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
    def flags(self):
        return u1(self.data[9:10])

    @cached_property
    def package_info(self):
        data = self.data[10:]
        aid_length = u1(data[2:3])
        return {'minor_version': u1(data[:1]),
                'major_version': u1(data[1:2]),
                'aid_length': aid_length,
                'aid': u1a(aid_length, data[3:])
                }

    @cached_property
    def package_name_info(self):
        try:
            data = self.data[self.package_info['aid_length']+13:]
            name_length = u1(data[:1])
            return {'name_length': name_length,
                    'name': u1a(name_length, data[1:])
                    }
        except IndexError:
            # field is optionnal
            return {'name_length': 0,
                    'name': ""
                    }

    def __str__(self):
        return "< Header:\n\tMagic: %08X\n\tVersion: %d.%d\n\tAID: %s\n>" % (
            self.magic,
            self.major_version, self.minor_version,
            stringify(self.package_info['aid'])
            )

class CAPFile(object):
    def __init__(self, path):
        self.path = path
        self.zipfile = zipfile.ZipFile(self.path, 'r')

    def _getFileName(self, component):
        for name in self.zipfile.namelist():
            if component in name:
                return name

    @cached_property
    def Header(self):
        return Header(self.zipfile.read(self._getFileName('Header')))


if __name__ == "__main__":
    import sys
    cap = CAPFile(sys.argv[1])
    print cap.Header
