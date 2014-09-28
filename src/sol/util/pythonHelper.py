""" Various utility functions

..note::
    some code copied from other projects, might not be related
"""
import re
import os
import errno
from collections import defaultdict


class regexdict(dict):
    """ Dict that return multiple values if the key is a regex
    """

    def __getitem__(self, regex):
        r = re.compile(regex)
        mkeys = filter(r.match, self.keys())
        for i in mkeys:
            yield (i, dict.__getitem__(self, i))


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

# Self nesting dict
Tree = lambda: defaultdict(Tree)
