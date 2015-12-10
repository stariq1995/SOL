# coding=utf-8


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
    url='https://bitbucket.org/progwriter/sol',
    setup_requires=['pytest-runner'],
    requires=['networkx', 'requests', 'netaddr', 'pytest', 'numpy', 'cython', 'six'],
    tests_require=['pytest'],
    ext_modules=cythonize("src/sol/**/*.pyx")
)
