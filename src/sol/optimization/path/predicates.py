# coding=utf-8
""" Implement predicates for path validity.
Both generic (example predicates) and some app-specific predicates
"""
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


def UseMboxModifier(path, topology):
    G = topology.getGraph()
    return [PathWithMbox(path, [n]) for n in path if 'hasmbox' in G.node[n]]