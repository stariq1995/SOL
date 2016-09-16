# coding=utf-8
# cython: profile=False
import cython
from sol.utils.ph import tup2str
from varnames cimport *


@cython.profile(False)
cpdef inline unicode xp(TrafficClass traffic_class, Path path, int epoch=0):
    """ Convenience method for formatting a decision variable

    :param traffic_class: the traffic class object, needed for the ID
    :returns: variable name of the form *x_classid_pathindex*
    :rtype: str
    """
    return 'x_{}_{}_{}'.format(traffic_class.ID, path.get_id(), epoch)

@cython.profile(False)
cpdef unicode al(TrafficClass traffic_class, int epoch=0):
    """
    Format an allocation variable

    :param traffic_class: the traffic class object
    :return: variable name of the form *a_classid*
    """
    return 'a_{}_{}'.format(traffic_class.ID, epoch)

cpdef unicode bn(int node):
    """
    Format a binary node variable

    :param node: nodeID
    :return: variable name of the form *binnode_nodeID*
    """
    return 'binnode_{}'.format(node)

cpdef unicode be(int head, int tail):
    """
    Format a binary edge variable

    :param head: edge head (nodeID)
    :param tail: edge tail (nodeID)
    :return: variable name of the form *binedge_headID_tailID*
    """
    return 'binedge_{}_{}'.format(head, tail)

@cython.profile(False)
cpdef unicode bp(TrafficClass traffic_class, Path path):
    """
    Format a binary path variable

    :param traffic_class: traffic class (for ID)
    :param pathIndex: path index in the list of paths per traffic class
    :return: variable name of the form *binpath_classid_pathindex*
    """
    return 'binpath_{}_{}'.format(traffic_class.ID, path.get_id())

cpdef unicode nl(int node, unicode resource, int epoch=0):
    """
    Format a node load variable

    :param node: node ID
    :param resource: the resource
    """
    return 'Load_{}_{}_{}'.format(resource, node, epoch)

cpdef unicode el(tuple link, unicode resource, int epoch=0):
    """
    Format a link load variable

    :param link:
    :param resource:
    """
    return 'Load_{}_{}_{}'.format(resource, tup2str(link), epoch)

cpdef unicode nc(int node, unicode resource, int epoch=0):
    """
    Format a capacity variable

    :param node:
    :param resource:
    """
    return 'Cap_{}_{}_{}'.format(resource, node, epoch)
