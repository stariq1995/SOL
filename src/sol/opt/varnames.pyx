# coding=utf-8
# cython: profile=False

import cython
from varnames cimport *

@cython.profile(False)
cpdef inline unicode xp(TrafficClass traffic_class, int path_index, int epoch):
    """ Convenience method for formatting the name of a decision variable

    :param traffic_class: the traffic class object, needed for the ID
    :returns: variable name of the form *x_classid_pathindex*
    :rtype: str
    """
    return u'x_{}_{}_{}'.format(traffic_class.ID, path_index, epoch)

@cython.profile(False)
cpdef inline unicode al(TrafficClass traffic_class, int epoch):
    """
    Format an allocation variable

    :param traffic_class: the traffic class object
    :param epoch: epoch number
    :return: variable name of the form *a_classid*
    """
    return u'a_{}_{}'.format(traffic_class.ID, epoch)

@cython.profile(False)
cpdef inline unicode bn(int node):
    """
    Format a binary node variable

    :param node: nodeID
    :return: variable name of the form *binnode_nodeID*
    """
    return u'binnode_{}'.format(node)

@cython.profile(False)
cpdef inline unicode be(int head, int tail):
    """
    Format a binary edge variable

    :param head: edge head (nodeID)
    :param tail: edge tail (nodeID)
    :return: variable name of the form *binedge_headID_tailID*
    """
    return u'binedge_{}_{}'.format(head, tail)

@cython.profile(False)
cpdef inline unicode bp(TrafficClass traffic_class, int path_index):
    """
    Format a binary path variable

    :param traffic_class: traffic class
    :param path_index: path index in the list of paths per traffic class
    :return: variable name of the form *binpath_classid_pathindex*
    """
    return u'binpath_{}_{}'.format(traffic_class.ID, path_index)
