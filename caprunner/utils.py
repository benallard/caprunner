import struct # for general decoding of class files

# Utility functions.

def u1(data):
    """
    unsigned on 1 byte
    >>> u1('\x67')
    103
    >>> u1('\x01\x02')
    1
    >>> u1('\x01\x55\x66\x66')
    1
    """
    return struct.unpack(">B", data[0:1])[0]

def u2(data):
    """
    unsigned on 2 bytes
    >>> u2('\x67')
    Traceback (most recent call last):
    ...
    error: unpack requires a string argument of length 2
    >>> u2('\x01\x02')
    258
    >>> u2('\x01\x55\x66\x66')
    341
    """
    return struct.unpack(">H", data[0:2])[0]

def u4(data):
    """
    unsigned on four bytes
    >>> u4('\x67')
    Traceback (most recent call last):
    ...
    error: unpack requires a string argument of length 4
    >>> u4('\x01\x02')
    Traceback (most recent call last):
    ...
    error: unpack requires a string argument of length 4
    >>> u4('\x01\x55\x66\x66')
    22373990
    """
    return struct.unpack(">L", data[0:4])[0]


def u1a(size, data):
    """
    u1 array
    >>> u1a(5, '\x45'*7)
    [69, 69, 69, 69, 69]
    """
    return [u1(data[i:i+1]) for i in xrange(size)]

def u2a(size, data):
    """
    u2 array
    >>> u2a(3, '\x78\x23\x89' * 2)
    [30755, 35192, 9097]
    """
    return [u2(data[i*2:i*2+2]) for i in xrange(size)]

def a2s(a):
    """
    array to string
    >>> a2s([0xa0, 0, 0, 0, 98, 0, 3])
    'A0 00 00 00 62 00 03'
    >>> a2s([-96])
    'A0'
    """
    return ' '.join(["%02X" % (i & 0xff) for i in a])

def s2a(s):
    """
    string to array
    >>> s2a('A0 00 00 00 62 00 03')
    [-96, 0, 0, 0, 98, 0, 3]
    """
    return [signed1(int(ss, 16)) for ss in s.split()]

def a2d(array):
    r"""
    array to data
    >>> a2d([0xa0, 0, 0, 0, 98, 0, 3])
    '\xa0\x00\x00\x00b\x00\x03'
    >>> a2d([-96])
    '\xa0'
    """
    return ''.join([chr(i & 0xff) for i in array])

def d2a(data):
    r"""
    data to array
    >>> d2a('\xa0\x00\x00\x00b\x00\x03')
    [-96, 0, 0, 0, 98, 0, 3]
    """
    return [signed1(ord(c)) for c in data]

def d2s(s):
    r"""
    data to string
    >>> d2s('\xa0\x00\x00\x00b\x00\x03')
    'A0 00 00 00 62 00 03'
    """
    return ' '.join(["%02X" % ord(c) for c in s])

def signed(value, depth):
    """
    return the signed value of the number on the specified depth
    """
    mask = (1 << (depth*8)) - 1
    if value > ((1 << (depth*8)-1) - 1):
        return -(~(value-1) & mask)
    else:
        return value

def signed1(value):
    """
    >>> signed1(0x7f)
    127
    >>> signed1(0x7e)
    126
    >>> signed1(0x02)
    2
    >>> signed1(0x01)
    1
    >>> signed1(0x00)
    0
    >>> signed1(0xff)
    -1
    >>> signed1(0xfe)
    -2
    >>> signed1(0x81)
    -127
    >>> signed1(0x80)
    -128
    """
    return signed(value, 1)

def signed2(value):
    """
    >>> signed2(0xffff)
    -1
    """
    return signed(value, 2)

def signed4(value):
    return signed(value, 4)
