# coding=utf-8
""" Various utility functions

..note::
    some code copied from other projects, might not be related
"""
import re
import os
import errno
from collections import defaultdict


class RegexDict(dict):
    """
    Dict that return multiple values on get operation if the key is a regex
    """

    def __getitem__(self, regex):
        """ Override the default get operation"""
        r = re.compile(regex)
        mkeys = filter(r.match, self.keys())
        for i in mkeys:
            yield (i, dict.__getitem__(self, i))


def rmRegex(dirname, pattern):
    """
    Remove files using a regex

    :param dirname: the directory from which we are removing files
    :param pattern: the regex. File names matching this regex within the
        directory will be removed
    """
    e = re.compile(pattern)
    for f in os.listdir(dirname):
        if e.search(f):
            os.remove(os.path.join(dirname, f))


def mkdirs(path):
    """
    Create nested directories, just like "mkdir -p"
    :param path: the name of directory to create
    :raise: OSError
    """
    try:
        os.makedirs(path)
    except OSError as exc:
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

# Self-nesting dict
Tree = lambda: defaultdict(Tree)
