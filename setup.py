# coding=utf-8

from distutils.core import setup, Command, Extension
from Cython.Build import cythonize

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(
    name='sol',
    version='0.4',
    package_dir={'': 'src'},
    packages=['sol'],
    author='Victor Heorhiadi',
    url='https://bitbucket.org/progwriter/sol',
    requires=['networkx', 'requests', 'netaddr', 'pytest', 'numpy', 'cython'],
    cmdclass={'test': PyTest},
    ext_modules = cythonize("src/sol/**/*.pyx")
)