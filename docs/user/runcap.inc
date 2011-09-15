.. -*-rst-*-

.. _runcap:

RunCAP
======

Overview
--------

Parameters
----------

.. _runcapcmds:

Command format
--------------

APDUs
^^^^^

APDU are sent to the CAP file in the following format::

    ==> se nd ap du;
    <== ex pe ct ed re tu rn co de;

Each byte is in hexadecimal format without ``0x`` preceding them.

If the CAP file returns another return code, the execution will stop.

Load command
^^^^^^^^^^^^

To load an applet into the interpreter, the following command has to
be used::

    load: /path/to/capfile.cap

The result of this command will be that the given CAP file will be
loaded into memory and its applets will be ready for the
:ref:`installcommand`. At this step, the whole CAP file will be
parsed.

.. _installcommand:

Install command
^^^^^^^^^^^^^^^

To install an applet into the interpreter, and make it selectable, the
following command has to be used::

    install: data : offset

The ``data`` is the one tramsmitted to :js:func:`Applet.install` [#ins]_
prepended with ``AIDlen || AID`` of the applet to install. The
``offset`` parameter indicate the offset of the ``AIDlen`` byte inside
the data.

Print the log
^^^^^^^^^^^^^

There is also a command to print an internal log of what happen during
the last APDU processing::

    log;

Example
^^^^^^^

The following example is used to test the HelloWorld example from the
JavaCard Development Kit.

.. literalinclude:: /user/helloworld.cmds
   :language: text
   :linenos:

* Line 1, the CAP file ``HelloWorld-2.1.2.cap`` is loaded inside the
  interpreter.
* Line 3, the applet with AID ``a0 00 00 00 62 03 01 0c 01 01`` is
  being installed. This applet is included inside the CAP file. The
  data transmitted to the function is constructed as follow:

  * First, the length of the AID on one byte: ``0a``
  * Then comes the AID itself ``a0 00 00 00 62 03 01 0c 01 01``
  * And finally the data to be transmitted to the
    :js:func:`Applet.install` function.

  As second parameter comes the offset of the AIDlength bytes, ``00``
  in our case as we did'nt gave junk data in the input.
* Line 5-6, the first APDU is being set to the Applet, namely a
  ``SELECT`` command with the AID of the installed applet. this select
  is processed by the interpreter and then by the Applet itself,
  returning some data.
* Line 8-9, a random command is processed by the Applet and some data
  is returned.

.. rubric:: Footnotes

.. [#ins] This is the concatenation of the following three fields,
   each one prepended with its own length (which is ``0`` if the field
   is empty)

   * instance AID (if not specified the applet AID will be taken)
   * control info
   * applet data
