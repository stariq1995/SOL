# coding=utf-8
"""
Implement predicates for path validity.
Both generic (example predicates) and some app-specific predicates
"""
import itertools

from sol.topology.topologynx cimport Topology

cpdef null_predicate(path, topology=None):
    """
    Predicate that allows every path

    :param path: the path to check
    :param topology:
    :returns: True"""
    return True

cpdef has_mbox_predicate(path, Topology topology):
    """
    This predicate checks if any switch in the path has a middlebox attached to it.

    :param path: the path in question
    :param topology: topology
    :return: True if at least one middlebox is present
    """
    return any([topology.has_middlebox(node) for node in path])

cpdef waypoint_mbox_predicate(path, Topology topology, order):
    """
    Check the path for correct waypoint enforcement through the middleboxes

    :param path: the path in question
    :param topology: topology
    :param order: a tuple contatining ordered service types. For example::
        ('fw', 'ids')

    :return: True if the path satisfies the desired waypoint order
    """
    return any([s == order
                for s in itertools.product(*[topology.get_service_types(node)
                                             for node in path.useMBoxes])])