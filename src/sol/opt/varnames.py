from sol.utils.pythonHelper import tup2str

LINKLOAD_PREFIX = 'LinkLoad'
LOAD_PREFIX = 'Load'


def xp(trafficClass, pathIndex):
    """ Convenience method for formatting a decision variable

    :param trafficClass: the traffic class object, needed for the ID
    :param pathIndex: index of the path in the list of paths per traffic class
    :returns: variable name of the form *x_classid_pathindex*
    :rtype: str
    """
    return 'x_{}_{}'.format(trafficClass.ID, pathIndex)


def al(trafficClass):
    """
    Format an allocation variable

    :param trafficClass: the traffic class object
    :return: variable name of the form *a_classid*
    """
    return 'a_{}'.format(trafficClass.ID)


def bn(node):
    """
    Format a binary node variable

    :param node: nodeID
    :return: variable name of the form *binnode_nodeID*
    """
    return 'binnode_{}'.format(node)


def be(head, tail):
    """
    Format a binary edge variable

    :param head: edge head (nodeID)
    :param tail: edge tail (nodeID)
    :return: variable name of the form *binedge_headID_tailID*
    """
    return 'binedge_{}_{}'.format(head, tail)


def bp(trafficClass, pathIndex):
    """
    Format a binary path variable

    :param trafficClass: traffic class (for ID)
    :param pathIndex: path index in the list of paths per traffic class
    :return: variable name of the form *binpath_classid_pathindex*
    """
    return 'binpath_{}_{}'.format(trafficClass.ID, pathIndex)


def nl(node, resource):
    """
    Format a node load variable

    :param node: node ID
    :param resource: the resource
    """
    return 'Load_{}_{}'.format(resource, node)


def el(link, resource):
    """
    Format a link load variable

    :param link:
    :param resource:
    """
    return 'Load_{}_{}'.format(resource, tup2str(link))


def nc(node, resource):
    """
    Format a capacity variable

    :param node:
    :param resource:
    """
    return 'Cap_{}_{}'.format(resource, node)
