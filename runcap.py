#!/usr/bin/python

from caprunner import resolver, capfile
from caprunner.utils import s2a, a2s
from caprunner.interpreter import JavaCardVM, ExecutionDone
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod

from pythoncard.framework import Applet, APDU, ISOException

applets = []

def myregister(*args):
    applets.append(args[0])

Applet.register = myregister

def main():
    import sys
    vm = JavaCardVM(resolver.linkResolver())
    cap_file = capfile.CAPFile(sys.argv[1])
    vm.load(cap_file)
    # create the applet
    for apl in cap_file.Applet.applets:
        vm.frame.push([0,0,11,0,1,2,3,4,5,6,7,8,9,10])
        vm.frame.push(0)
        vm.frame.push(3)
        vm._invokestaticjava(JavaCardStaticMethod(apl.install_method_offset, vm.cap_file, vm.resolver))
        try:
            while True:
                vm.step()
        except ISOException, ie:
            sw = ie.getReason()
            print "instanciating throwed : %02X %02X" % ((sw & 0xff00) >> 8, sw & 0x00ff)
        except ExecutionDone:
            pass

    for line in sys.stdin:
        print "==>", line[:-1]
        # decode from hex to data
        data = s2a(line)
        # Make an APDU object
        apdu = APDU(data)
        # pass to the process method
        vm.frame.push(applets[0])
        vm.frame.push(apdu)
        # invoke the process method
        vm._invokevirtualjava(JavaCardVirtualMethod(applets[0]._ref.offset, 7, vm.cap_file, vm.resolver))
        try:
            while True:
                vm.step()
        except ExecutionDone:
            pass
        except ISOException, ie:
            sw = ie.getReason()
            print "<== %02X %02X" % ((sw & 0xff00) >> 8, sw & 0x00ff)
            continue
        # get the result
        buf = apdu._APDU__buffer[:apdu._outgoinglength]
        buf.extend([0x90, 0x00])
        print "<==", a2s(buf)

if __name__ == "__main__":
    main()
