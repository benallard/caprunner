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
    """
    return ' '.join(["%02X" % i for i in a])

def a2d(array):
    r"""
    array to data
    >>> a2d([0xa0, 0, 0, 0, 98, 0, 3])
    '\xa0\x00\x00\x00b\x00\x03'
    """
    return ''.join([chr(i) for i in array])

def d2s(s):
    r"""
    data to string
    >>> d2s('\xa0\x00\x00\x00b\x00\x03')
    'A0 00 00 00 62 00 03'
    """
    return ' '.join(["%02X" % ord(c) for c in s])
