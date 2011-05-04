#!/usr/bin/python

import sys

from caprunner import resolver, capfile
from caprunner.utils import s2a, a2s, d2a, a2d, signed1
from caprunner.interpreter import JavaCardVM, ExecutionDone
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod, NoSuchMethod

from pythoncard.framework import Applet, APDU, ISOException

current_install_aid = None
applets = {}
selected = None

def myregister(applet, *args):
    if len(args) == 0:
        applets[a2d(current_install_aid)] = applet

Applet.register = myregister

def process(vm, send, receive):

    print send[:4]
    if send[:4] == [00, -92, 0x04, 00]:
        aid = send[5:5 + send[4]]
        print "select command : %s" % a2s(aid)
        # select command
        select(vm, aid)

    global selected
    print "==> %s" % a2s(send)
    # Make an APDU object
    apdu = APDU(send)
    # pass to the process method
    vm.frame.push(selected)
    vm.frame.push(apdu)
    # invoke the process method
    vm._invokevirtualjava(JavaCardVirtualMethod(selected._ref.offset, 7, vm.cap_file, vm.resolver))
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
    global selected
    vm.frame.push(selected)
    vm._invokevirtualjava(JavaCardVirtualMethod(selected._ref.offset, 4, vm.cap_file, vm.resolver))
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass
    selected = None

def select(vm, aid):
    global selected
    if selected is not None:
        deselect(vm)
    vm.frame.push(applets[a2d(aid)])
    try:
        selectmtd = JavaCardVirtualMethod(applets[a2d(aid)]._ref.offset, 6, vm.cap_file, vm.resolver)
    except NoSuchMethod:
        return
    vm._invokevirtualjava(selectmtd)
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass
    if vm.frame.getValue() == True:
        selected = applets[a2d(aid)]

def install(vm, data, offset):
    global current_install_aid
    aidlen = data[offset]
    offset += 1
    aid = data[offset: offset + aidlen]
    offset += aidlen
    length = data[offset]
    offset += 1
    vm.frame.push(data)
    vm.frame.push(offset)
    vm.frame.push(length)
    applet = None
    for apl in vm.cap_file.Applet.applets:
        if a2d(aid) == a2d(apl.aid):
            applet = apl
            break
    if applet is None:
        print "No Applet installed ; %s not found" % a2s(aid)
        return
    current_install_aid = aid
    vm._invokestaticjava(JavaCardStaticMethod(applet.install_method_offset, vm.cap_file, vm.resolver))
    try:
        while True:
            vm.step()
    except ISOException, ie:
        sw = ie.getReason()
        print "instanciating throwed : %02X %02X" % ((sw & 0xff00) >> 8, sw & 0x00ff)
    except ExecutionDone:
        pass
    current_install_aid = None

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
            print line[sep1:sep2]
            data = s2a(line[sep1:sep2])
            offset = s2a(line[sep2 + 1:])[0]
            install(vm, data, offset)
        elif line.startswith('load:'):
            vm.load(capfile.CAPFile(line[5:].strip()))
        else:
            print line

if __name__ == "__main__":
    main()
