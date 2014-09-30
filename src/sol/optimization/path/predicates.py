""" Implement predicates for path validity.
Both generic (example predicates) and some app-specific predicates
"""
from panacea.lps.topology.traffic import PathWithMbox

__author__ = 'victor'


# noinspection PyUnusedLocal
def nullPredicate(path, topology=None):
    """
    Predicate that allows every path

    :param path: the path to check
    :param topology:
    :returns: True"""
    return True


def SIMPLEPredicate(path, topology):
    """
    SIMPLE predicate.

    :param path: the path to check
    :param topology: topology on which we are operating
    :return: True if the paths is valid, false otherwise
    """
    G = topology.getGraph()
    return any([('hasmbox' in G.node[n]) for n in path])


def SIMPLEModifier(path, topology):
    G = topology.getGraph()
    return [PathWithMbox(path, [n]) for n in path if 'hasmbox' in G.node[n]]



    # def merlinPredicate(path, topology):
    # """ Merlin predicate
    #
    #     :param path: the path to check
    #     :param topology: the topology we are operating on
    #     :return: True if the path is valid, False otherwise
    #     """
    #     return len([n for n in path if topology.isMiddlebox(n)]) > 0


    # def waypointPredicate(path, topology, order):
    #     """ The waypoint enforcement predicate
    #
    #     .. note::
    #        This relies on topology nodes having a 'type' attribute.
    #
    #     :param path: the path to check
    #     :param topology: topology on which we are operation on
    #     :param order: a list of nodes types, in order they should be traversed
    #     :returns: True if the path is valid, False otherwise
    #     """
    #     G = topology.getGraph()
    #     types = [G.node[n]['mtype'] for n in path if 'mtype' in G.node[n]]
    #     return all(map(eq, types, order))


    # noinspection PyUnusedLocal
    # def lengthPredicate(path, topology=None, length=3):
    #     """ Predicate that checks the length of the path (must match exactly)
    #
    #     :param path: the path to check
    #     :param topology:
    #     :param length:
    #     :returns: True if length of the path matches the expected length
    #     """
    #     return len(path) == length