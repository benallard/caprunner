opnamepar = {
    # code: (mnemonic, parameter_length, parameter_sizes)
    36: ("aaload", 0, ()),
    55: ("aastore", 0, ()),
    1: ("aconst_null", 0, ()),
    21: ("aload", 1, (1,)),
    24: ("aload_0", 0, ()),
    25: ("aload_1", 0, ()),
    26: ("aload_2", 0, ()),
    27: ("aload_3", 0, ()),
    145: ("anewarray", 2, (2,)),
    119: ("areturn", 0, ()),
    146: ("arraylength", 0, ()),
    40: ("astore", 1, (1,)),
    43: ("astore_0", 0, ()),
    44: ("astore_1", 0, ()),
    45: ("astore_2", 0, ()),
    46: ("astore_3", 0, ()),
    147: ("athrow", 0, ()),
    37: ("baload", 0, ()),
    56: ("bastore", 0, ()),
    18: ("bipush", 1, ()),
    16: ("bspush", 1, ()),
    148: ("checkcast", 3, (1, 2,)),
    61:("dup", 0, ()),
    63:("dup_x", 1, (1,)),
    62: ("dup2", 0, ()),
    131: ("getfield_a", 1, (1,)),
    173: ("getfield_a_this", 1, (1,)),
    169: ("getfield_a_w", 2, (2,)),
    132: ("getfield_b", 1, (1,)),
    174: ("getfield_b_this", 1, (1,)),
    170: ("getfield_b_w", 2, (2,)),
    134: ("getfield_i", 1, (1,)),
    176: ("getfield_i_this", 1, (1,)),
    172: ("getfield_i_w", 2, (2,)),
    133: ("getfield_s", 1, (1,)),
    175: ("getfield_s_this", 1, (1,)),
    171: ("getfield_s_w", 2, (2,)),
    123: ("getstatic_a", 2, (2,)),
    124: ("getstatic_b", 2, (2,)),
    126: ("getstatic_i", 2, (2,)),
    125: ("getstatic_s", 2, (2,)),
    112: ("goto", 1, (1,)),
    168: ("goto_w", 2, (2,)),
    93: ("i2b", 0, ()),
    94: ("i2s", 0, ()),
    66: ("iadd", 0, ()),
    39: ("iaload", 0, ()),
    84: ("iand", 0, ()),
    58: ("iastore", 0, ()),
    95: ("icmp", 0, ()),
    10: ("iconst_0", 0, ()),
    11: ("iconst_1", 0, ()),
    12: ("iconst_2", 0, ()),
    13: ("iconst_3", 0, ()),
    14: ("iconst_4", 0, ()),
    15: ("iconst_5", 0, ()),
    9: ("iconst_m1", 0, ()),
    72: ("idiv", 0, ()),
    104: ("ifacmpeq", 1, (1,)),
    160: ("ifacmpeq_w", 2, (2,)),
    105: ("ifacmpne", 1, (1,)),
    161: ("ifacmpne_w", 2, (2,)),
    106: ("ifscmpeq", 1, (1,)),
    162: ("ifscmpeq_w", 2, (2,)),
    109: ("ifscmpge", 1, (1,)),
    165: ("ifscmpge_w", 2, (2,)),
    110: ("ifscmpgt", 1, (1,)),
    166: ("ifscmpgt_w", 2, (2,)),
    111: ("ifscmple", 1, (1,)),
    167: ("ifscmple_w", 2, (2,)),
    108: ("ifscmplt", 1, (1,)),
    164: ("ifscmplt_w", 2, (2,)),
    107: ("ifscmpne", 1, (1,)),
    163: ("ifscmpne_w", 2, (2,)),
    96: ("ifeq", 1, (1,)),
    152: ("ifeq_w", 2, (2,)),
    99: ("ifge", 1, (1,)),
    155: ("ifge_w", 2, (2,)),
    100: ("ifgt", 1, (1,)),
    156: ("ifgt_w", 2, (2,)),
    101: ("ifle", 1, (1,)),
    157: ("ifle_w", 2, (2,)),
    98: ("iflt", 1, (1,)),
    154: ("iflt_w", 2, (2,)),
    97: ("ifne", 1, (1,)),
    153: ("ifne_w", 2, (2,)),
    103: ("ifnonnull", 1, (1,)),
    159: ("ifnonnull_w", 2, (2,)),
    102: ("ifnull", 1, (1,)),
    158: ("ifnull_w", 2, (2,)),
    90: ("iinc", 2, (1, 1,)),
    151: ("iinc_w", 3, (1, 2,)),
    20: ("iipush", 4, (4,)),
    23: ("iload", 1, (1,)),
    32: ("iload_0", 0, ()),
    33: ("iload_1", 0, ()),
    34: ("iload_2", 0, ()),
    35: ("iload_3", 0, ()),
    118: ("ilookupswitch", None, (2, 2,)), # variable number of arguments !!!
    70: ("imul", 0, ()),
    76: ("ineg", 0, ()),
    149: ("instanceof", 3, (1, 2,)),
    142: ("invokeinterface", 4, (1, 2, 1,)),
    140: ("invokespecial", 2, (2,)),
    141: ("invokestatic", 2, (2,)),
    139: ("invokevirtual", 2, (2,)),
    86: ("ior", 0, ()),
    74: ("irem", 0, ()),
    121: ("ireturn", 0, ()),
    78: ("ishl", 0, ()),
    80: ("ishr", 0, ()),
    42: ("istore", 1, (1,)),
    51: ("istore_0", 0, ()),
    52: ("istore_1", 0, ()),
    53: ("istore_2", 0, ()),
    54: ("istore_3", 0, ()),
    68: ("isub", 0, ()),
    116: ("itableswitch", None, (2, 4, 4,)),
    82: ("iushr", 0, ()),
    88: ("ixor", 0, ()),
    113: ("jsr", 2, (2,)),
    143: ("new", 2, (2,)),
    144: ("newarray", 1, (1,)),
    0: ("nop", 0, ()),
    59: ("pop", 0, ()),
    60: ("pop2", 0, ()),
    135: ("putfield_a", 1, (1,)),
    181: ("putfield_a_this", 1, (1,)),
    177: ("putfield_a_w", 2, (2,)),
    136: ("putfield_b", 1, (1,)),
    182: ("putfield_b_this", 1, (1,)),
    178: ("putfield_b_w", 2, (2,)),
    138: ("putfield_i", 1, (1,)),
    184: ("putfield_i_this", 1, (1,)),
    180: ("putfield_i_w", 2, (2,)),
    137: ("putfield_s", 1, (1,)),
    183: ("putfield_s_this", 1, (1,)),
    179: ("putfield_s_w", 2, (2,)),
    127: ("putstatic_a", 2, (2,)),
    128: ("putstatic_b", 2, (2,)),
    130: ("putstatic_i", 2, (2,)),
    129: ("putstatic_s", 2, (2,)),
    114: ("ret", 1, (1,)),
    122: ("return", 0, ()),
    91: ("s2b", 0, ()),
    92: ("s2i", 0, ()),
    65: ("sadd", 0, ()),
    38: ("saload", 0, ()),
    83: ("sand", 0, ()),
    57: ("sastore", 0, ()),
    3: ("sconst_0", 0, ()),
    4: ("sconst_1", 0, ()),
    5: ("sconst_2", 0, ()),
    6: ("sconst_3", 0, ()),
    7: ("sconst_4", 0, ()),
    8: ("sconst_5", 0, ()),
    2: ("sconst_m1", 0, ()),
    71: ("sdiv", 0, ()),
    89: ("sinc", 2, (1, 1,)),
    150: ("sinc_w", 3, (1, 2,)),
    19: ("sipush", 2, (2,)),
    22: ("sload", 1, (1,)),
    28: ("sload_0", 0, ()),
    29: ("sload_1", 0, ()),
    30: ("sload_2", 0, ()),
    31: ("sload_3", 0, ()),
    117: ("slookupswitch", None, (2, 2,)),
    69: ("smul", 0, ()),
    75: ("sneg", 0, ()),
    85: ("sor", 0, ()),
    73: ("srem", 0, ()),
    120: ("sreturn", 0, ()),
    77: ("sshl", 0, ()),
    79: ("sshr", 0, ()),
    17: ("sspush", 2, (2,)),
    41: ("sstore", 1, (1,)),
    47: ("sstore_0", 0, ()),
    48: ("sstore_1", 0, ()),
    49: ("sstore_2", 0, ()),
    50: ("sstore_3", 0, ()),
    67: ("ssub", 0, ()),
    115: ("stableswitch", None, (2, 2, 2,)),
    81: ("sushr", 0, ()),
    64: ("swap_x", 1, (1,)),
    87: ("sxor", 0, ()),
}

opcode = {}
opname = {}
oppar = {}
opparams = {}
for code, field in opnamepar.iteritems():
    opcode[field[0]] = code
    opname[code] = field[0]
    oppar[code] = field[1]
    opparams[code] = field[2]

def u1(data):
    return data[0]

def u2(data):
    return (data[0] << 8) + data[1]

def u4(data):
    return (data[0] << 24) + (data[1] << 16) + (data[2] << 8) + data[3]

def getPar(data):

    code = data[0]
    if code == opcode["ilookupswitch"]:
        npairs = u2(data[3:5])
        return npairs*6 + 4
    elif code == opcode["itableswitch"]:
        lowbytes = u4(data[3:7])
        highbytes = u4(data[7:11])
        return (highbytes - lowbytes + 1)*2 + 10
    elif code == opcode["slookupswitch"]:
        npairs = u2(data[3:5])
        return npairs*4 + 4
    elif code == opcode["stableswitch"]:
        lowbytes = u2(data[3:5])
        highbytes = u2(data[5:7])
        return (highbytes - lowbytes + 1)*2 + 6
    else:
        return oppar[code]

def disassemble(data):
    code = 0
    while data:
        code = data[0]
        par = getPar(data)
        yield opname[code]
        ofs = 1
        for p in opparams[code]:
            if p == 1:
                yield str(u1(data[ofs:]))
            elif p == 2:
                yield str(u2(data[ofs:]))
            elif p == 4:
                yield str(u4(data[ofs:]))
            ofs += p
        data = data[par+1:]

