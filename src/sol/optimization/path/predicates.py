# coding=utf-8
""" Implement predicates for path validity.
Both generic (example predicates) and some app-specific predicates
"""
import itertools
from sol.optimization.topology.traffic import PathWithMbox


# noinspection PyUnusedLocal
def nullPredicate(path, topology=None):
    """
    Predicate that allows every path

    :param path: the path to check
    :param topology:
    :returns: True"""
    return True


def useMboxModifier(path, topology, chainLength=1):
    """
    Path modifier function. Expands one path into multiple paths, based on how many intermediate
    middleboxes are used.

    :param path: the path containing switch node IDs
    :param topology: the topology we are working with
    :param chainLength: how many middleboxes are required
    :return: a list of paths, note the special
        :py:class:`~sol.optimization.topology.traffic.PathWithMbox` object

    .. note::
        This with expand a single path into :math:`{n \\choose chainLength}` paths where :math:`n` is
        the number of switches with middleboxes attached to them in the current path.
    """
    return [PathWithMbox(path, chain) for chain in itertools.combinations(path, chainLength)
            if all([topology.hasMbox(n) for n in chain])]


def hasMboxPredicate(path, topology):
    """
    This predicate checks if any switch in the path has a middlebox attached to it.

    :param path: the path in question
    :param topology: topology
    :return: True if at least one middlebox is present
    """
    return any([topology.hasMbox(node) for node in path])