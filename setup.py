# coding=utf-8
from distutils.core import setup
from distutils.extension import Extension

import numpy
from Cython.Build import cythonize

ext = [Extension('*', sources=["src/sol/**/*.pyx"],
                 include_dirs=[numpy.get_include()],
                 define_macros=[('CYTHON_TRACE', '1')])]

setup(
    name='sol',
    version='0.5',
    description='SOL: SDN Optimization Layer',

    author='Victor Heorhiadi',
    author_email='victor@cs.unc.edu',

    package_dir={'': 'src'},
    packages=['sol'],
    url='https://github.com/progwriter/SOL',
    requires=['networkx', 'requests', 'netaddr', 'numpy', 'cython', 'six',
              'bitstring'],
    ext_modules=cythonize(ext, compiler_directives={
        'cdivision': True,
        'embedsignature': True,
    }),
    package_data={'sol': ['*.pxd']}
)
