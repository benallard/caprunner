import struct # for general decoding of class files

# Utility functions.

def u1(data):
    return struct.unpack(">B", data[0:1])[0]

def u2(data):
    return struct.unpack(">H", data[0:2])[0]

def u4(data):
    return struct.unpack(">L", data[0:4])[0]

def s2(data):
    return struct.unpack(">h", data[0:2])[0]

def s4(data):
    return struct.unpack(">l", data[0:4])[0]

def s8(data):
    return struct.unpack(">q", data[0:8])[0]

def f4(data):
    return struct.unpack(">f", data[0:4])[0]

def f8(data):
    return struct.unpack(">d", data[0:8])[0]

def u1a(size, data):
    """ u1 array """
    return [u1(data[i:i+1]) for i in xrange(size)]

def u2a(size, data):
    """ u2 array """
    return [u2(data[i*2:i*2+2]) for i in xrange(size)]

def a2s(a):
    """ array to string """
    return ' '.join(["%02X" % i for i in a])

def a2d(array):
    """
    >>> a2d([160, 0, 0, 0, 98, 0, 3])
    '\xa0\x00\x00\x00b\x00\x03'
    """
    return ''.join([chr(i) for i in array])

def stringify(s):
    return ' '.join(["%02X" % ord(c) for c in s])
