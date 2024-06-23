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
        else:
            version = tuple([int(i) for i in sys.argv[2].split('.')])
            print("Running in version %s.%s.%s" % version)
            cap_file = sys.argv[1]

        self.cap = CAPFile(cap_file)
        self.resolver = resolver.linkResolver(version)

    def toJasmin(self, opname, params, class_name, class_methods, classs, class_index, offsetInMethod, method_name):
        constPool = self.cap.ConstantPool
        imports =  self.cap.Import
        staticFields =  self.cap.StaticField
        descs = self.cap.Descriptor
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
                if class_methods:
                    for method in class_methods:
                        if method.location == cst.static_method_ref.offset:
                            method_name = str(dbg.strings_table[method.name_index])
                            method_type = str(dbg.strings_table[method.descriptor_index])
                            return f'{opname} {class_name}/{method_name}{method_type}'
                    raise KeyError('Didn\'t find method')
                else:
                    for cidx_desc, class_desc in enumerate(descs.classes):
                        if cidx_desc == class_index:
                            for method_idx, method in enumerate(class_desc.methods):
                                if method.method_offset == cst.static_method_ref.offset:
                                    method_type_idx = method.type_offset
                                    method_type_str = self.type_to_str(method_type_idx, True)
                                    method_name = f'Method{method_idx}'
                                    return f'{opname} class{class_index}/{method_name}{method_type_str}'
                    raise KeyError('Didn\'t find method')
        elif opname == 'new':
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 1:
                raise KeyError('wrong tag')

            if cst.isExternal:
                pkg = imports.packages[cst.class_ref.package_token]
                pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                clsname = pkg_ref.getClassName(cst.class_ref.class_token)
                return f'{opname} {pkg_ref.name}/{clsname}'
            else:
                if dbg:
                    for classs in dbg.classes:
                        if classs.location == cst.class_ref:
                            clsname = str(dbg.strings_table[classs.name_index])
                            return f'{opname} {clsname}'
                    raise KeyError('Didn\'t find class')
                else:
                    return f'{opname} class{cst.class_ref}'
        elif opname.startswith('putfield'):
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 2:
                raise KeyError('wrong tag')
            if dbg:
                for classs in dbg.classes:
                        if classs.location == cst.class_ref:
                            clsname = str(dbg.strings_table[classs.name_index])
                            field = classs.fields[index]
                            field_name =  str(dbg.strings_table[field.name_index])
                            field_type =  str(dbg.strings_table[field.descriptor_index])
                            return f'putfield {clsname}/{field_name} {field_type}'
            else:
                for cidx_desc, class_desc in enumerate(descs.classes):
                        if cidx_desc == class_index:
                            for field in class_desc.fields:
                                if field.instance_field.class_ref == cst.class_ref:
                                    type_idx = field.type
                                    field_type = self.type_to_str(type_idx)
                                    return f'putfield class{cst.class_ref}/field{index} {field_type}'

            raise KeyError('Didn\'t find class')
        elif opname == 'returnn':
            return 'return'
        elif opname.startswith('sstore') or opname.startswith('sload') or opname.startswith('sconst'):
            if len(params) >0 :
                return f'i{opname[1:]} {params[0]}'
            return f'i{opname[1:]}'
        elif opname in('sadd', 'sand', 'ssub', 'smul', ):
            return f'i{opname[1:]}'
        elif opname == 'sinc':
            return f'iinc {params[0]} {params[1]}'
        elif opname == 'sspush':
            return f'sipush {params[0]}'
        elif opname == 'dup_x':
            m = (params[0] & 0xf0) >> 4
            n = (params[0] & 0xf)
            if m == 1 and n == 2:
                return 'dup_x1'
            else:
                NotImplementedError('dup_x not fully implemented')
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
            if opname.endswith('_w'):
                added_offset = signed2(params[0])
            else:
                added_offset = signed1(params[0])
            if opname.startswith('if'):
                if opname[3] == 's':
                    opname=opname[:3]+'i'+opname[4:]
                if opname.endswith('_w'):
                    opname= opname[:-2]

            offset = offsetInMethod + added_offset
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
        elif opname.startswith('getfield'):
            index = params[0]
            cst = constPool.constant_pool[index]
            if cst.tag != 2:
                raise KeyError(f'wrong tag {cst.tag} expected 2')

            if dbg:
                for classs in dbg.classes:
                        if classs.location == cst.class_ref:
                            clsname = str(dbg.strings_table[classs.name_index])
                            field = classs.fields[cst.token]
                            field_name =  str(dbg.strings_table[field.name_index])
                            field_type =  str(dbg.strings_table[field.descriptor_index])
                            if opname.endswith('_this'):
                                return f'aload_0\n\tgetfield {clsname}/{field_name} {field_type}'
                            else:
                                return f'getfield {clsname}/{field_name} {field_type}'
                
                raise KeyError('Cannot Find the field')
            else:
                clsname = f'class{cst.class_ref}'
                for cidx_desc, class_desc in enumerate(descs.classes):
                        if cidx_desc == cst.class_ref:
                            field = class_desc.fields[cst.token]
                            type_idx = field.type
                            field_type = self.type_to_str(type_idx)
                            if opname.endswith('_this'):
                                return f'getfield {clsname}/field{cst.token} {field_type}'
                            else:
                                return f'getfield {clsname}/field{cst.token} {field_type}'
                raise KeyError('Cannot Find the field')

    def type_to_str(self, type_idx, is_method = False):
        descs = self.cap.Descriptor
        imports = self.cap.Import
        if type_idx == 2:
            type_str = 'Z'
        elif type_idx == 3:
            type_str = 'B'
        elif type_idx == 4:
            type_str = 'S'
        elif type_idx == 5:
            type_str = 'I'
        else:
            type_res = descs.types.type_desc[type_idx].jasimstr()
            type_str = ''
            if is_method:
                type_str = '('

            res_idx = 0
            while res_idx < len(type_res):
                if type_res[res_idx] in ['ref','[ref']:
                    prefix = ''
                    if type_res[res_idx] == '[ref':
                        prefix = '['
                    res_idx += 1
                    p, c = type_res[res_idx].split('.')
                    pkg = imports.packages[int(p)]
                    pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                    class_name = pkg_ref.getClassName(int(c))
                    if res_idx >= len(type_res) - 1 and is_method:
                        type_str+=')'
                    type_str += f'{prefix}L{pkg_ref.name}/{class_name}'
                else:
                    if res_idx >= len(type_res) - 1 and is_method:
                        type_str+=')'
                    type_str += type_res[res_idx]

                res_idx+=1
        return type_str

    def parse_method(self, class_file, method, class_name, class_methods, classs, class_index, method_name):
        offsetInMethod = 0
        if not method.method_info.isAbstract:
            code = method.bytecodes
            previous_getfield_this = False
            while len(code) > 0: 
                opname = bytecode.opname[code[0]]
                instrsize, params = bytecode.getParams(code)
                code = code [instrsize:]
                moreinf = self.toJasmin(opname, params, class_name, class_methods, classs, class_index, offsetInMethod, method_name)
                if moreinf:
                    if previous_getfield_this:
                        class_file.write(f'\tL{method_name}{offsetInMethod+1}:\n {moreinf}\n')
                        previous_getfield_this = False
                    else:
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

                if opname.startswith('getfield') and opname.endswith('_this'):
                    previous_getfield_this =True
                offsetInMethod += instrsize
            class_file.write('.end method\n')

    def parse(self):
        methods = self.cap.Method
        if self.cap.Debug is not None:
            dbg = self.cap.Debug
            classes = dbg.classes
        else:
            dbg = None
            classes = self.cap.Class
            imports = self.cap.Import
            const_pool = self.cap.ConstantPool
            descs = self.cap.Descriptor
        for cidx , classs in classes.classes.items():
            if dbg:
                class_name = str(dbg.strings_table[classs.name_index])
            else:
                class_name = f'class{cidx}'
            with open(f'./{class_name}.j', 'w') as class_file:
                class_file.write(f'.class public {class_name}\n')
                if dbg:
                    super_name = str(dbg.strings_table[classs.superclass_name_index])
                else:
                    super_cls = classs.super_class_ref
                    if super_cls.isExternal:
                        pkg = imports.packages[super_cls.class_ref.package_token]
                        pkg_ref = self.resolver.refs[a2d(pkg.aid)]
                        super_name = pkg_ref.getClassName(super_cls.class_ref.class_token)
                        super_name = f'{pkg_ref.name}/{super_name}'

                class_file.write(f'.super {super_name}\n\n')
                if dbg:
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
                            self.parse_method(class_file, method, class_name, classs.methods, None, classs, method_name)
                else:
                    for cidx_desc, class_desc in enumerate(descs.classes):
                        if cidx_desc == cidx:
                            for field in class_desc.fields:
                                if field.instance_field.class_ref == cidx:
                                    type_idx = field.type
                                    type_str = self.type_to_str(type_idx)
                                    if field.isStatic:
                                        class_file.write(f'.field static public static_field{field.instance_field.token} {type_str}\n')
                                    else:
                                        class_file.write(f'.field public field{field.instance_field.token} {type_str}\n')

                            for method_idx, method in enumerate(class_desc.methods):
                                method_offset = method.method_offset
                                method_token = method.token
                                method_type_idx = method.type_offset
                                method_type_str = self.type_to_str(method_type_idx, True)
                                method_name = f'Method{method_idx}'
                                class_file.write(f'\n.method {method_name}{method_type_str}\n')
                                method = methods.methods[method_offset]
                                self.parse_method(class_file, method, class_name, None, None, cidx, method_name)

            print(f'Finished {class_name}')

fp = fullParse()
fp.parse()