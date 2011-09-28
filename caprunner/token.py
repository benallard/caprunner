"""
This is a Python token, it reprsents a Token + the CardManager

"""

from pythoncard.framework import Applet, ISO7816, ISOException, APDU, JCSystem, AID

from caprunner import resolver, capfile
from caprunner.utils import d2a, a2d, a2s, signed1
from caprunner.interpreter import JavaCardVM, ExecutionDone
from caprunner.interpreter.methods import JavaCardStaticMethod, JavaCardVirtualMethod, NoSuchMethod

class Token(object):
    """
    This token is a Java Token. 
    The Applet is actually a capfile. The code below is taken from runcap.py
    """
    def __init__(self, jcversion = (3,0,1)):

        self.current_applet_aid = None
        # a2d(aid) => Applet
        self.applets = {}
        # channel => Applet
        self.selected = [None, None, None, None]
        # opened
        self.channels = [True, False, False, False]
        # current one
        self.current_channel = 0

        # Create the VM
        self.vm = JavaCardVM(resolver.linkResolver(jcversion))

        self.installJCFunctions()

    def echo(self, *args, **kwargs):
        # to be redefined in the subclassing class
        pass

    def installJCFunctions(self):
        """ This tweak the JC Framework to make it fit our environment 
        We make a big usage of closures to pass the local `self` to the JC
        functions
        """

        def defineMyregister(self):
            def myregister(applet, bArray = [], bOffset=0, bLength=0):
                if bLength != 0:
                    aid = bArray[bOffset:bOffset + bLength]
                    # also update the current one
                    self.current_applet_aid = aid
                else:
                    aid = self.current_applet_aid
                self.applets[a2d(aid)] = applet
                self.echo("registered %s as %s" % (a2s(aid), applet))
            return myregister
        Applet.register = defineMyregister(self)

        def defineMygetAID(self):
            def mygetAID():
                return AID(self.current_applet_aid, 0, len(self.current_applet_aid))
            return mygetAID
        JCSystem.getAID = defineMygetAID(self)
        Applet.getAID = JCSystem.getAID

        def defineMylookupAID(self):
            def mylookupAID(buffer, offset, length):
                if a2d(buffer[offset:offset + length]) in self.applets:
                    return AID(buffer, offset, length)
                return None
            return mylookupAID
        JCSystem.lookupAID = defineMylookupAID(self)

        def defineMyisAppletActive(self):
            def myisAppletActive(aid):
                return self.applets[a2d(aid.aid)] in self.selected
            return myisAppletActive
        JCSystem.isAppletActive = defineMyisAppletActive(self)

        def defineMygetAssignedChannel(self):
            def mygetAssignedChannel():
                return self.current_channel
            return mygetAssignedChannel
        JCSystem.getAssignedChannel = defineMygetAssignedChannel(self)

    def transmit(self, bytes):
        self.vm.log = ""
        self.current_channel = bytes[0] & 0x3
        if self.selected[self.current_channel]:
            self.selected[self.current_channel]._selectingApplet = False
        if not bool(bytes[0] & 0x80):
            # ISO command
            if bytes[1:4] == [-92, 4, 0]:
                aid = bytes[5:5 + bytes[4]]
                # select command A4 04 00
                if not self._cmselect(aid):
                    return d2a('\x69\x99')
            elif bytes[1:4] == [112, 0, 0]:
                # open channel : 70 00 00
                for idx in xrange(4):
                    if not self.channels[idx]:
                        self.channels[idx] = True
                        buf = [idx]
                        buf.extend(d2a('\x90\x00'))
                        return buf
                return d2a(ISO7816.SW_WRONG_P1P2)
            elif bytes[1:3] == [112, -128]:
                # close channel: 70 80
                idx = bytes[3]
                if self.channels[idx]:
                    self.channels[idx] = False
                    return d2a('\x90\x00')
                return d2a(ISO7816.SW_WRONG_P1P2)
            elif bytes[1:4] == [-26, 12, 0]:
                # install : E6 0C 00
                self.install(bytes, 5)

        applet = self.selected[self.current_channel]
        if applet is None:
            # no applet selected on current channel
            return d2a(ISO7816.SW_FILE_NOT_FOUND)
        # Make an APDU object
        apdu = APDU(bytes)
        # pass to the process method
        self.vm.frame.push(applet)
        self.vm.frame.push(apdu)
        # invoke the process method
        self.vm._invokevirtualjava(JavaCardVirtualMethod(
                applet._ref.offset,
                7, # process
                False,
                self.vm.cap_file,
                self.vm.resolver))
        try:
            while True:
                self.vm.step()
        except ExecutionDone:
            pass
        except ISOException, isoe:
            sw = isoe.getReason()
            return [signed1((sw & 0xff00) >> 8), signed1(sw & 0x00ff)]
#        except:
            self.echo("Caught bad exception")
            return d2a('\x6f\x00')
            raise
        buf = apdu._APDU__buffer[:apdu._outgoinglength]
        buf.extend(d2a('\x90\x00'))
        return buf

    def _cmdeselect(self):
        channel = self.current_channel
        applet = self.selected[channel]
        self.vm.frame.push(applet)
        try:
            deselectmtd = JavaCardVirtualMethod(
                applet._ref.offset,
                4,
                False,
                self.vm.cap_file,
                self.vm.resolver)
        except NoSuchMethod:
            self.selected[channel] = None
            return True
        self.vm._invokevirtualjava(deselectmtd)
        try:
            while True:
                self.vm.step()
        except ExecutionDone:
            pass
        if self.vm.frame.getValue():
            self.selected[channel] = None
            return True
        return False

    def _cmselect(self, aid):
        channel = self.current_channel
       
        applet = self.selected[channel]
        if applet is not None:
            if not self._cmdeselect():
                self.echo("Deselect failed")
                return False

        # We should spend some time looking for an applet there ...
        try:
            potential = self.applets[a2d(aid)]
        except KeyError:
            self.echo("Applet not found", self.applets)
            return False

        self.vm.frame.push(potential)
        try:
            selectmtd = JavaCardVirtualMethod(
                potential._ref.offset,
                6,
                False,
                self.vm.cap_file,
                self.vm.resolver)
        except NoSuchMethod:
            self.selected[channel] = potential
            self.selected[channel]._selectingApplet = True
            return True
        self.vm._invokevirtualjava(selectmtd)
        try:
            while True:
                self.vm.step()
        except ExecutionDone:
            pass
        if self.vm.frame.getValue() == True:
            self.selected[channel] = potential
            self.selected[channel]._selectingApplet = True
            return True
        else:
            return False

    def install(self, data, offset):
        """ 
        data[offset:] is len||appletaid||len||installdata
        where installdata is the data given to the install method
        """
        aidlen = data[offset]
        offset += 1
        aid = data[offset: offset + aidlen]
        offset += aidlen
        length = data[offset]
        offset += 1
        # data[offset:offset+length] is what is given to the install JavaCard 
        # method which means: len-instanceaid-len-stuff-len-customparams
        # where instance AID might be empty
        self.vm.frame.push(data)
        self.vm.frame.push(offset)
        self.vm.frame.push(length)
        applet = None
        self.echo(len(self.vm.cap_file.Applet.applets))
        for apl in self.vm.cap_file.Applet.applets:
            if a2d(aid) == a2d(apl.aid):
                applet = apl
                break
        if applet is None:
            self.echo("Applet %s not found in the CAP file" % a2s(aid))
            return
        self.current_applet_aid = aid
        self.vm._invokestaticjava(JavaCardStaticMethod(
                applet.install_method_offset,
                self.vm.cap_file,
                self.vm.resolver))
        try:
            while True:
                self.vm.step()
        except ISOException, ie:
            sw = isoe.getReason()
            return [signed1((sw & 0xff00) >> 8), signed1(sw & 0x00ff)]
        except ExecutionDone:
            pass
        self.current_install_aid = None
        return d2a('\x90\x00')
