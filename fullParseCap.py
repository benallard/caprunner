#!/usr/bin/env python

import sys

from caprunner.capfile import CAPFile
import caprunner.resolver as resolver
import caprunner.bytecode as bytecode
from caprunner.interpreter.methods import PythonStaticMethod, JavaCardStaticMethod, PythonVirtualMethod, JavaCardVirtualMethod
from caprunner.utils import a2d, signed1, signed2, signed4
class fullParse:
    def __init__(self) -> None:
        if len(sys.argv) != 3:
            print('fullParsecap.py capfile version')
            sys.exit(-1)
        version = tuple([int(i) for i in sys.argv[2].split('.')])
        print("Running in version %s.%s.%s" % version)
        cap_file = sys.argv[1]
        self.cap = CAPFile(cap_file)
        self.resolver = resolver.linkResolver(version)

    def toJasmin(self, opname, params, class_name, class_methods, offsetInMethod, method_name):
        constPool = self.cap.ConstantPool
        imports =  self.cap.Import
        staticFields =  self.cap.StaticField
        dbg =self.cap.Debug
        if opname == 'invokestatic':
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 6:
                raise Exception('wrong tag')
            if cst.isExternal:
                pkg = imports.packages[cst.static_method_ref.package_token]
                pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                (clsname, mtd) = pkg_ref.getStaticMethod(cst.static_method_ref.class_token, cst.static_method_ref.token)
                mtdname = mtd['name']
                mtdtype = mtd['type']
                return f'{opname} {pkg_ref.name}/{clsname}/{mtdname}{mtdtype}'
            else:
                raise NotImplementedError('cannot invoke static non external yet')
        elif opname == 'invokevirtual':
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 3:
                raise KeyError('wrong tag')
            if cst.isExternal:
                pkg = imports.packages[cst.class_ref.package_token]
                pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                (clsname, mtd) = pkg_ref.getVirtualMethod(cst.class_ref.class_token, cst.token)
                mtdname = mtd['name']
                mtdtype = mtd['type']
                return f'{opname} {pkg_ref.name}/{clsname}/{mtdname}{mtdtype}'
            else:
                raise NotImplementedError('cannot invoke virtual non external yet')
        elif opname == 'invokespecial':
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 6:
                raise KeyError('wrong tag')
            if cst.isExternal:
                pkg = imports.packages[cst.static_method_ref.package_token]
                pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                (clsname, mtd) = pkg_ref.getStaticMethod(cst.static_method_ref.class_token, cst.static_method_ref.token)
                mtdname = mtd['name']
                mtdtype = mtd['type']
                return f'{opname} {pkg_ref.name}/{clsname}/{mtdname}{mtdtype}'
            else:
                for method in class_methods:
                    if method.location == cst.static_method_ref.offset:
                        method_name = str(dbg.strings_table[method.name_index])
                        method_type = str(dbg.strings_table[method.descriptor_index])
                        return f'{opname} {class_name}/{method_name}{method_type}'
                raise KeyError('Didn\'t find method')
        elif opname == 'new':
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 1:
                raise KeyError('wrong tag')
            if cst.isExternal:
                pkg = imports.packages[cst.class_ref.package_token]
                pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                clsname = pkg.getClassName(cst.class_ref.class_token)
                return f'{opname} {pkg_ref.name}/{clsname}'
            else:
                for classs in dbg.classes:
                    if classs.location == cst.class_ref:
                        clsname = str(dbg.strings_table[classs.name_index])
                        return f'{opname} {clsname}'
                raise KeyError('Didn\'t find class')

        elif opname.startswith('putfield'):
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 2:
                raise KeyError('wrong tag')
            for classs in dbg.classes:
                    if classs.location == cst.class_ref:
                        clsname = str(dbg.strings_table[classs.name_index])
                        field = classs.fields[index]
                        field_name =  str(dbg.strings_table[field.name_index])
                        field_type =  str(dbg.strings_table[field.descriptor_index])
                        return f'putfield {clsname}/{field_name} {field_type}'
            raise KeyError('Didn\'t find class')
        elif opname == 'returnn':
            return 'return'
        elif opname.startswith('sstore') or opname.startswith('sload') or opname.startswith('sconst'):
            if len(params) >0 :
                return f'i{opname[1:]} {params[0]}'
            return f'i{opname[1:]}'
        elif opname in('sadd', 'sand', 'ssub'):
            return f'i{opname[1:]}'
        elif opname == 'sspush':
            return f'sipush {params[0]}'
        elif opname == 's2b':
            return f'i2b'
        elif opname == 'bspush':
            if params[0] > 127:
                return f'sipush {params[0]}'
            return f'bipush {params[0]}'
        elif 'static' in opname:
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 5:
                raise KeyError('wrong tag')
            if cst.isExternal:
                raise NotImplementedError('static external not implemented')
            else: 
                offset = cst.static_field_ref.offset
                for classs in dbg.classes:
                    for field in classs.fields:
                        if field.location == offset:
                            field_name =  str(dbg.strings_table[field.name_index])
                            field_type =  str(dbg.strings_table[field.descriptor_index])
                            class_name_for_class = str(dbg.strings_table[classs.name_index])
                            return f'{opname[:-2]} {class_name_for_class}/{field_name} {field_type};'

                raise KeyError('cant find field')
        elif opname == 'slookupswitch':
            output = 'lookupswitch'
            default_offset = params[0]
            num_val = params[1]
            sorted_cases= sorted(params[2:], key=lambda tup: tup[0])
            for (val, offset) in sorted_cases:
                if val > 255:
                    val = '0x'+hex(val)[-2:]
                else:
                    val = hex(val)
                output+= f'\n\t\t{val} : L{method_name}{offsetInMethod+offset}'
            output += f'\n\t\tdefault : L{method_name}{offsetInMethod+default_offset}'
            return output
        elif opname.startswith('if') or opname.startswith('goto'):
            if opname.startswith('if'):
                if opname[3] == 's':
                    opname=opname[:3]+'i'+opname[4:]
                if opname.endswith('_w'):
                    opname= opname[:-2]
            
            offset = offsetInMethod + params[0]
            return f'{opname} L{method_name}{offset}'
        elif opname == 'newarray':
            array_type = None
            if params[0] == 10:
                array_type = 'bool'
            elif params[0] == 11:
                array_type = 'byte'
            elif params[0] == 12:
                array_type = 'short'
            elif params[0] == 13:
                array_type = 'int'
            else:
                raise KeyError(f'unknown array type {params[0]}')
            return f'{opname} {array_type}'
        elif opname.startswith('getfield') and opname.endswith('_this'):
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 2:
                raise KeyError(f'wrong tag {cst.tag} expected 2')
            for classs in dbg.classes:
                    if classs.location == cst.class_ref:
                        clsname = str(dbg.strings_table[classs.name_index])
                        field = classs.fields[index]
                        field_name =  str(dbg.strings_table[field.name_index])
                        field_type =  str(dbg.strings_table[field.descriptor_index])
                        return f'aload_0\n\tgetfield {clsname}/{field_name} {field_type}'
            
            raise KeyError('Cannot Find the field')


    def parse(self):
        methods = self.cap.Method
        dbg = self.cap.Debug
        for classs in dbg.classes:
            
            class_name = str(dbg.strings_table[classs.name_index])
            with open(f'./{class_name}.j', 'w') as class_file:
                class_file.write(f'.class public {class_name}\n')
                super_name = str(dbg.strings_table[classs.superclass_name_index])
                class_file.write(f'.super {super_name}\n\n')
                for field in classs.fields:
                    field_name =  str(dbg.strings_table[field.name_index])
                    field_type =  str(dbg.strings_table[field.descriptor_index])
                    if (field.access_flags & 0x0010): #ACC_FINAL
                        field_value = field.constant_value
                        if (field.access_flags & 0x0008):# static
                            class_file.write(f'.field public static final {field_name} {field_type} = {field_value}\n')
                        else:
                            class_file.write(f'.field public final {field_name} {field_type} = {field_value}\n')
                    else:
                        if (field.access_flags & 0x0008):# static
                            class_file.write(f'.field static public {field_name} {field_type}\n')

                        else:
                            class_file.write(f'.field public {field_name} {field_type}\n')
                
                if classs.methods:

                    for method_start in classs.methods:
                        method = methods.methods[method_start.location]
                        method_name = str(dbg.strings_table[method_start.name_index])
                        method_type = str(dbg.strings_table[method_start.descriptor_index])
                        class_file.write(f'\n.method {method_name}{method_type}')
                        class_file.write(f'\n.limit locals {method.method_info.max_locals}')
                        class_file.write(f'\n.limit stack {method.method_info.max_stack}\n')

                        offsetInMethod = 0
                        if not method.method_info.isAbstract:
                            code = method.bytecodes
                            while len(code) > 0: 
                                opname = bytecode.opname[code[0]]
                                instrsize, params = bytecode.getParams(code)
                                code = code [instrsize:]
                                moreinf = self.toJasmin(opname, params, class_name, classs.methods, offsetInMethod, method_name)
                                if moreinf:
                                    class_file.write(f'\tL{method_name}{offsetInMethod}:\n {moreinf}\n')
                                
                                else:
                                    if params:
                                        param_str = ''
                                        for param in params:
                                            param_str += str(param)+ ' '
                                        param_str = param_str[:-1]
                                        class_file.write(f'\tL{method_name}{offsetInMethod}:\n {opname} {param_str}\n')
                                    else:
                                        class_file.write(f'\tL{method_name}{offsetInMethod}:\n {opname}\n')
                                offsetInMethod += instrsize
                            class_file.write('.end method\n')
            print(f'Finished {class_name}')

fp = fullParse()
fp.parse()