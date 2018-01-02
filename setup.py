# coding=utf-8

import numpy
from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension


ext = [
    Extension(
        'sol.opt.app',
        ['src/sol/opt/app.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.opt.composer',
        ['src/sol/opt/composer.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.opt.funcs',
        ['src/sol/opt/funcs.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.opt.gurobiwrapper',
        ['src/sol/opt/gurobiwrapper.pyx'],
        include_dirs=[numpy.get_include()],
        define_macros=[('CYTHON_TRACE', 1),
                       ('CYTHON_TRACE_NOGIL', 1)]
    ),
    Extension(
        'sol.opt.varnames',
        ['src/sol/opt/varnames.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.path.generate',
        ['src/sol/path/generate.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.path.paths',
        ['src/sol/path/paths.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.path.predicates',
        ['src/sol/path/predicates.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.path.select',
        ['src/sol/path/select.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.topology.provisioning',
        ['src/sol/topology/provisioning.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.topology.topologynx',
        ['src/sol/topology/topologynx.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.topology.traffic',
        ['src/sol/topology/traffic.pyx'],
        include_dirs=[numpy.get_include()]
    ),
    Extension(
        'sol.utils.ph',
        ['src/sol/utils/ph.pyx'],
        include_dirs=[numpy.get_include()]
    ),
]
setup(
    name='sol',
    version='0.9.1',
    description='SOL: SDN Optimization Layer',
    keywords=['sdn', 'network', 'optimization', 'framework', 'research', 'sol'],

    author='Victor Heorhiadi',
    author_email='victor@cs.unc.edu',
    license='MIT',

    package_dir={'': 'src'},
    packages=['sol'],
    url='https://github.com/progwriter/SOL',
    requires=['networkx', 'requests', 'netaddr', 'numpy', 'cython', 'six'],
    tests_require=['pytest', 'hypothesis', "flake8"],

    ext_modules=cythonize(ext, compiler_directives={
        'cdivision': True,
        'embedsignature': True,
        'boundscheck': False,
        'binding': True,
        'linetrace': True
    }),
    package_data={'sol': ['__init__.pxd']},
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Topic :: System :: Networking',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]

)
