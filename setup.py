# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

version = '1.0'

setup(
    name='CAPRunner',
    version=version,
    author='Benoît Allard',
    author_email='benoit.allard@gmx.de',
    description='A JavaCard bytecode emulator',
    long_description=open('README.rst').read(),
    url='https://bitbucket.org/benallard/caprunner',
    packages=['caprunner', 'caprunner.interpreter'],
    scripts=['runcap.py', 'genref.py', 'readcap.py', 'readexp.py'],
    install_requires=['JavaCard'],
    license='LGPL',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Testing',
    ],
    keywords='javacard bytecode emulator CAP EXP applet',
)
