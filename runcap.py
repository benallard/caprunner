#!/usr/bin/python

import sys

from caprunner import resolver, capfile
from caprunner.utils import s2a, a2s, d2a, a2d, signed1
from caprunner.interpreter import JavaCardVM, ExecutionDone
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod, NoSuchMethod

from pythoncard.framework import Applet, APDU, ISOException, JCSystem, AID

current_install_aid = None
# a2d(aid) => Applet
applets = {}
# channel => Applet
selected = [None, None, None, None]
# opened
channels = [True, False, False, False]
# current one
current_channel = 0

def myregister(applet, *args):
    if len(args) == 0:
        applets[a2d(current_install_aid)] = applet

Applet.register = myregister

def mylookupAID(buffer, offset, length):
    if a2d(buffer[offset:offset + length]) in applets:
        return AID(buffer, offset, length)
    return None

JCSystem.lookupAID = mylookupAID

def myisAppletActive(aid):
    return applets[a2d(aid.aid)] in selected

JCSystem.isAppletActive = myisAppletActive

def mygetAssignedChannel():
    return current_channel
    
JCSystem.getAssignedChannel = mygetAssignedChannel

def process(vm, send, receive):
    vm.log = ""
    global current_channel
    current_channel = send[0] & 0x3
    if selected[current_channel]:
        selected[current_channel]._selectingApplet = False
    if not bool(send[0] & 0x80):
        # ISO command
        if send[1:4] == [-92, 4, 0]:
            aid = send[5:5 + send[4]]
            print "select command : %s" % a2s(aid)
            # select command
            select(vm, current_channel, aid)
        elif send[1:4] == [112, 0, 0]:
            # open channel
            for idx in xrange(4):
                if not channels[idx]:
                    channels[idx] = True
                    buf = [idx]
                    buf.extend(d2a('\x90\x00'))
                    if buf != receive:
                        print "<== %02X 90 00 (%s)" % (idx, a2s(receive))
                        sys.exit()
                    return
            print "No more channels"
            sys.exit()
        elif send[1:3] == [112, -128]:
            if channels[current_channel]:
                channels[current_channel] = False
                buf = d2a('\x90\x00')
                if buf != receive:
                    print "<== %02X 90 00 (%s)" % (idx, a2s(receive))
                    sys.exit()
                return
            else:
                print "Channel %d not opened" % send[3]
                sys.exit()

    print "==> %s" % a2s(send)
    # Make an APDU object
    apdu = APDU(send)
    # pass to the process method
    applet = selected[current_channel]
    vm.frame.push(applet)
    vm.frame.push(apdu)
    # invoke the process method
    vm._invokevirtualjava(JavaCardVirtualMethod(applet._ref.offset, 7, False, vm.cap_file, vm.resolver))
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
    print "<== %s" % a2s(buf)
    if buf != receive:
        print "<== %s was expected" % a2s(receive)
        print vm.log
        print buf
        print receive
        sys.exit()

def deselect(vm, channel):
    applet = selected[channel]
    vm.frame.push(applet)
    vm._invokevirtualjava(JavaCardVirtualMethod(applet._ref.offset, 4, False, vm.cap_file, vm.resolver))
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass
    return vm.frame.getValue()

def select(vm, channel, aid):
    applet = selected[channel]
    if applet is not None:
        if not deselect(vm, channel):
            return False
    try:
        vm.frame.push(applets[a2d(aid)])
    except KeyError:
        return False
    try:
        selectmtd = JavaCardVirtualMethod(applets[a2d(aid)]._ref.offset, 6, False, vm.cap_file, vm.resolver)
    except NoSuchMethod:
        selected[channel] = applets[a2d(aid)]
        selected[channel]._selectingApplet = True
        return True
    vm._invokevirtualjava(selectmtd)
    try:
        while True:
            vm.step()
    except ExecutionDone:
        pass
    if vm.frame.getValue() == True:
        selected[channel] = applets[a2d(aid)]
        selected[channel]._selectingApplet = True
        return True
    else:
        return False

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
        elif line.startswith('install:'):
            sep1 = 8
            sep2 = line.find(':', sep1+1)
            data = s2a(line[sep1:sep2])
            offset = s2a(line[sep2 + 1:])[0]
            install(vm, data, offset)
        elif line.startswith('load:'):
            vm.load(capfile.CAPFile(line[5:].strip()))
        elif line.startswith('log;'):
            print vm.log
        else:
            print line

if __name__ == "__main__":
    main()
