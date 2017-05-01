# coding=utf-8
# from distutils.core import setup
# from distutils.extension import Extension
from setuptools import setup
from setuptools.extension import Extension

import numpy
from Cython.Build import cythonize

ext = [Extension('*', sources=["src/sol/**/*.pyx"],
                 include_dirs=[numpy.get_include()],
                 #  define_macros=[('CYTHON_TRACE', 1),
                 # ('CYTHON_TRACE_NOGIL', 1)]
                 )]

req = None
with open('requirements.txt') as r:
    req = r.readlines()

setup(
    name='sol',
    version='0.9',
    description='SOL: SDN Optimization Layer',


    author='Victor Heorhiadi',
    author_email='victor@cs.unc.edu',

    package_dir={'': 'src'},
    packages=['sol'],
    url='https://github.com/progwriter/SOL',
    # requires=['networkx', 'requests', 'netaddr', 'numpy', 'cython', 'six',
    #           'bitstring', 'gurobi'],
    requires=req,
    # test_requires=['pytest', 'hypothesis'],
    ext_modules=cythonize(ext, compiler_directives={
        'cdivision': True,
        'embedsignature': True,
        'boundscheck': False
    }),
    package_data={'sol': ['__init__.pxd']}
)
