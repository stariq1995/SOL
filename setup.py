# coding=utf-8

from distutils.core import setup

setup(
    name='sol',
    version='1.1',
    package_dir={'': 'src'},
    packages=['sol'],
    author='Victor Heorhiadi',
    url='https://bitbucket.org/progwriter/sol',
    requires=['networkx', 'requests', 'netaddr', 'pytest', 'numpy']
)