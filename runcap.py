#!/usr/bin/python

import sys

from caprunner import resolver, capfile
from caprunner.utils import s2a, a2s, d2a, signed1
from caprunner.interpreter import JavaCardVM, ExecutionDone
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod, NoSuchMethod

from pythoncard.framework import Applet, APDU, ISOException

applets = []

def myregister(*args):
    applets.append(args[0])

Applet.register = myregister

def process(vm, send, receive):
    print "==> %s" % a2s(send)
    # Make an APDU object
    apdu = APDU(send)
    # pass to the process method
    vm.frame.push(applets[0])
    vm.frame.push(apdu)
    # invoke the process method
    vm._invokevirtualjava(JavaCardVirtualMethod(applets[0]._ref.offset, 7, vm.cap_file, vm.resolver))
    isoE = False
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass
    except ISOException, ie:
        sw = ie.getReason()
        buf = [signed1((sw & 0xff00) >> 8), signed1(sw & 0x00ff)]
        isoE = True
    if not isoE:
        buf = apdu._APDU__buffer[:apdu._outgoinglength]
        buf.extend(d2a('\x90\x00'))
    if buf != receive:
        print "<== %s (%s)" % (a2s(buf), a2s(receive))
        sys.exit()

def deselect(vm):
    vm.frame.push(applets[0])
    vm._invokevirtualjava(JavaCardVirtualMethod(applets[0]._ref.offset, 4, vm.cap_file, vm.resolver))
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass

def select(vm):
    vm.frame.push(applets[0])
    try:
        selectmtd = JavaCardVirtualMethod(applets[0]._ref.offset, 6, vm.cap_file, vm.resolver)
    except NoSuchMethod:
        return
    vm._invokevirtualjava(selectmtd)
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass

def install(vm, data, offset, length):
        vm.frame.push(data)
        vm.frame.push(offset)
        vm.frame.push(length)
        apl = vm.cap_file.Applet.applets[0]
        vm._invokestaticjava(JavaCardStaticMethod(apl.install_method_offset, vm.cap_file, vm.resolver))
        try:
            while True:
                vm.step()
        except ISOException, ie:
            sw = ie.getReason()
            print "instanciating throwed : %02X %02X" % ((sw & 0xff00) >> 8, sw & 0x00ff)
        except ExecutionDone:
            pass

def main():
    vm = JavaCardVM(resolver.linkResolver())

    send = []
    receive = []
    for line in sys.stdin:
        line = line.strip()
        if len(line) == 0 and len(send) != 0 and len(receive) != 0:
            process(vm, send, receive)
            send = []
            receive = []
        if line[:4] == "==> ":
            send.extend(s2a(line[4:]))
        elif line[:4] == "<== ":
            receive.extend(s2a(line[4:]))
        elif line.startswith('deselect;'):
            deselect(vm)
        elif line.startswith('select;'):
            select(vm)
        elif line.startswith('install:'):
            sep1 = 8
            sep2 = line.find(':', sep1+1)
            sep3 = line.find(':', sep2+1)
            print line[sep1:sep2]
            data = s2a(line[sep1:sep2])
            print line[sep2+1:sep3]
            offset = s2a(line[sep2 + 1:sep3])[0]
            length = s2a(line[sep3 + 1:])
            install(vm, data, offset, length)
        elif line.startswith('load:'):
            vm.load(capfile.CAPFile(line[5:].strip()))
        else:
            print line

if __name__ == "__main__":
    main()
