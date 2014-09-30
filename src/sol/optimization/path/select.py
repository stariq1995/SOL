""" Module implements different path pruning strategies
"""
from collections import defaultdict
import random


def chooserand(ppk, numPaths):
    """ Chooses a number of paths uniformly at random

    :param ppk: paths per commodity
    :param numPaths: number of paths to pick per commodity
    :return: the new (chosen) paths per each commodity
    :rtype: dict
    """
    newppk = {}
    for comm in ppk:
        if len(ppk[comm]) > numPaths:
            newppk[comm] = random.sample(ppk[comm], numPaths)
        else:
            newppk[comm] = ppk[comm]
    return newppk


def sortPathsPerCommodity(ppk, key=None, inplace=True):
    """
    Sort paths per commodity

    :param ppk: ppk
    :param key: criteria to sort by. If none, path length is used
    :param inplace: sort in place. If False, new sorted ppk is returned.
    :return: New ppk if *inplace=False* otherwise None
    """
    if key is None:
        key = len
    if inplace:
        for k in ppk:
            ppk[k].sort(key=len)
    else:
        newppk = {}
        for k in ppk:
            newppk[k] = sorted(ppk[k], key=key)
        return newppk


def kShortestPaths(ppk, numPaths, needsSorting=True, inplace=True):
    """ Chooses K shortest paths
    :param ppk: paths per commodity
    :param numPaths: number of paths to choose (k) per commodity
    :param needsSorting: whether we need to sort the paths first
    :param inplace: if *needsSorting* is True, whether to sort the ppk in
        place or make a copy
    :return: the new (chosen) paths per commodity
    :rtype: dict
    """
    newppk = None
    if needsSorting:
        newppk = sortPathsPerCommodity(ppk, key=len, inplace=inplace)
    if newppk is None:
        newppk = ppk
    result = {}
    for comm in ppk:
        result[comm] = newppk[comm][:numPaths]
    return result


def filterPaths(ppk, func):
    """
    Filter paths using a function.

    :param ppk: paths per commodity
    :param func: function to be applied to each path
    :return: new paths per commodity with paths for which *func* returned a
        true value
    """
    assert (hasattr(func, '__call__'))
    result = defaultdict(lambda: [])
    for k in ppk:
        for path in ppk[k]:
            if func(path):
                result[k].append(path)
    return result
