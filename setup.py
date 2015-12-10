# coding=utf-8

from Cython.Build import cythonize
from setuptools import setup, Extension

setup(
    name='sol',
    version='0.5',
    package_dir={'': 'src'},
    packages=['sol'],
    author='Victor Heorhiadi',
    author_email='victor@cs.unc.edu',
    description='SOL: SDN Optimization Layer',
    url='https://bitbucket.org/progwriter/sol',
    setup_requires=['pytest-runner'],
    requires=['networkx', 'requests', 'netaddr', 'pytest', 'numpy', 'cython', 'six'],
    tests_require=['pytest'],
    ext_modules=cythonize(Extension('solc', "src/sol/**/*.pyx"))
)
