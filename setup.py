# coding=utf-8
import numpy
from Cython.Build import cythonize
from distutils.core import setup

setup(
    name='sol',
    version='0.5',
    description='SOL: SDN Optimization Layer',

    author='Victor Heorhiadi',
    author_email='victor@cs.unc.edu',

    package_dir={'': 'src'},
    packages=['sol'],
    url='https://github.com/progwriter/SOL',
    requires=['networkx', 'requests', 'netaddr', 'numpy', 'cython', 'six'],
    ext_modules=cythonize("src/sol/**/*.pyx", compiler_directives={
        'cdivision':True,
        # 'profile': True
        'embedsignature': True
    }),
    include_dirs=[numpy.get_include()]
)
