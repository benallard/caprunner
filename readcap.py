#!/usr/bin/env python

import sys

from caprunner.capfile import CAPFile

cap = CAPFile(sys.argv[1])
print cap.Header
print cap.Directory
if cap.Applet is not None:
    print cap.Applet
print cap.Import
print cap.ConstantPool
print cap.Class
print cap.Method
print cap.StaticField
print cap.RefLocation
if cap.Export is not None:
    print cap.Export
print cap.Descriptor
if cap.Debug is not None:
    print cap.Debug
