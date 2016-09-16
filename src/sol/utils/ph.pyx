# coding=utf-8
""" Various utility functions

.. note::
    Some code copied from other projects, might not be related
"""
import itertools
from collections import defaultdict
import warnings

cpdef unicode tup2str(tuple t):
    """ Convert tuple to string

    :param t: the tuple
    """
    return '_'.join(map(str, t))

# Self-nesting dict
Tree = lambda: defaultdict(Tree)


def listeq(a, b):
    """
        Checks that two lists have equal elements
    """
    return len(a) == len(b) and all([x == y for x, y in itertools.izip(a, b)])

def parse_bool(s):
    """ Parse a string into a boolean. Multiple truth values are supported,
    such as 'true', 'yes', 'y' and even 'ok' """
    return s.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'ok']