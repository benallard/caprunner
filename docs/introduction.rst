
Introduction
============

Motivation
----------

This project was born when a need appeared for a JavaCard Applet simulator that
would let us have a look at the internal bits such as maximum stack depth,
memory used, ... A first idea was to parse the Java source file and interpret
it. This idea quickly disapeared in flavor of CAP file parsing and execution.
This way, we take the exact same imput as the smartcard for a result as
comparable as possible. The CAP file parser was born.

Overview
--------

The main component of this package is :program:`runcap.py`, a little script
(less than 300 lines) that agregate the included libs into a CAP file executer.
This script has dependencies on pythoncard_ which provide the basic OS
functionnalities of the JavaCard.

.. _pythoncard: https://bitbucket.org/benallard/pythoncard

Integration
-----------

Thie project takes part of the WebSCard_ project. This particular part cares that SmartCard can be emulated without the need of a physical one.

.. _WebSCard: https://bitbucket.org/benallard/webscard

Document structure
------------------

This document is split into two parts: The :ref:`usermanual` and the
:ref:`developermanual`.

As a user you a probably only interested in the first one, as a developper, both
one should be of interest. The :ref:`developermanual` will go more into details
on how to build your application using part of the CAPRunner.

