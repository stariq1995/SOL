""" Various utility functions

..note::
    some code copied from other projects, might not be related
"""
import struct
import re
import os
import errno
from collections import defaultdict


class smartdict(dict):
    """ Dict that nests itself instead of throwing the KeyError
    """

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


class regexdict(dict):
    """ Dict that return multiple values if the key is a regex
    """

    def __getitem__(self, regex):
        r = re.compile(regex)
        mkeys = filter(r.match, self.keys())
        for i in mkeys:
            yield (i, dict.__getitem__(self, i))


def b2i(stuff):
    """

    :param stuff:
    :return:
    """
    return struct.unpack('<I', stuff)[0]


def b2f(stuff):
    """

    :param stuff:
    :return:
    """
    return struct.unpack('<f', stuff)[0]


def nb2i(stuff):
    """

    :param stuff:
    :return:
    """
    return struct.unpack('!I', stuff)[0]


def i2nb(stuff):
    """

    :param stuff:
    :return:
    """
    return struct.pack('!I', stuff)


def ip2i(s):
    """Convert dotted IPv4 address to integer.
    :param s:
    """
    return reduce(lambda a, b: a << 8 | b, map(int, s.split(".")))


def i2ip(ip):
    """Convert 32-bit integer to dotted IPv4 address.
    :param ip:
    """
    return ".".join(map(lambda n: str(ip >> n & 0xFF), [24, 16, 8, 0]))


def t1(x):
    """

    :param x:
    :return:
    """
    return x[0]


def t2(x):
    """

    :param x:
    :return:
    """
    return x[1]


def rmRegex(dirName, pattern):
    """

    :param dirName:
    :param pattern:
    """
    e = re.compile(pattern)
    for f in os.listdir(dirName):
        if e.search(f):
            os.remove(os.path.join(dirName, f))


def mkdirs(path):
    """

    :param path:
    :raise:
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def flatten2d(st):
    """

    :param st:
    :return:
    """
    return [st[i][e] for i in st.iterkeys() for e in st[i].iterkeys()]


def tup2str(t):
    """ Convert tuple to string
    :param t:
    """
    return '_'.join(map(str, t))


def str2tup(s, d='_'):
    """ Convert string to tuple
    :param s: string
    :param d: delimiter
    :return: tuple
    """
    return tuple(s.split(d))


def ishell():
    """ Call up the IPython shell
    """
    from IPython.terminal.embed import InteractiveShellEmbed

    ipshell = InteractiveShellEmbed(
        banner1='Dropping into IPython',
        exit_msg='Leaving Interpreter, back to program.')
    ipshell('Debug Time!')


# Self nesting dict
Tree = lambda: defaultdict(Tree)

if __name__ == "__main__":
    print "This only has utility functions. Import, do not run"
