# coding=utf-8
""" Implement predicates for path validity.
Both generic (example predicates) and some app-specific predicates
"""
import itertools
from sol.optimization.topology.traffic import PathWithMbox

__author__ = 'victor'


# noinspection PyUnusedLocal
def nullPredicate(path, topology=None):
    """
    Predicate that allows every path

    :param path: the path to check
    :param topology:
    :returns: True"""
    return True


def useMboxModifier(path, topology, chainLength=1):
    return [PathWithMbox(path, chain) for chain in itertools.combinations(path, chainLength)
            if all([topology.hasMbox(n) for n in chain])]

def hasMboxPredicate(path, topology):
    return any([topology.hasMbox(node) for node in path])