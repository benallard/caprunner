.. -*-rst-*-

.. _installation:

Installation
============

From the README:

Installation
------------

Your best chance for the moment is to clone the repository using `Mercurial`_ to a local directory::

    $ hg clone https://bitbucket.org/benallard/caprunner/

This will create a copy of the repository in a ``caprunner`` directory.

In order to get the dependencies right, I suggest you also clone their repositories (the second one is optionnal)::

    $ hg clone https://bitbucket.org/benallard/pythoncard/
    $ hg clone https://bitbucket.org/benallard/pythonplatform/

Finally, the easiest way to get the dependencies resolved is to *copy* (or *link* on UNIX) the following directories at the root of the ``caprunner`` directory:

* ``python``, ``pythoncard`` and ``pythoncardx`` from the pythoncard directory
* and (optionnaly) ``org`` from the pythonplatform directory.

.. _`Mercurial`: http://mercurial.selenic.com/

Getting started
---------------

As a final step, you will need to ``compile`` the export files used during compilation of your applet into a JSON file. This step is needed in order to not read every single export file at each startup.

This is done with the following command line::

    $ python caprunner/refcollection.py --dump dump.json /path/to/export_files

This will generate a file called ``dump.json`` containing the necessary information from the export files. The path given as second parameter is the directory containing the export files from your JavaCard Development Kit (e.g. the ``api21_export_files`` directory for a JavaCard 2.1.2).

CAPRunner will expect the generated json file to be called ``<JavaCard version>.json``

Finally, you should be able to launch ``runcap.py``. By default, it will emulate a JavaCard Classic 3.0.1, if you need another version, just give it as parameter. For instance::

    $ ./runcap.py 2.1.2

Starting from here, ``runcap`` will wait for your orders. Please refer to the :ref:`runcapcmds` for the format of the order to send to ``runcap``.
