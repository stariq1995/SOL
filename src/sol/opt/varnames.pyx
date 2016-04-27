# coding=utf-8
from sol.utils.pythonHelper import tup2str
from varnames cimport *

LINKLOAD_PREFIX = 'LinkLoad'
LOAD_PREFIX = 'Load'

MIN_LINK_LOAD = 'minlinkload'
MIN_NODE_LOAD = 'minnodeload'
MIN_LATENCY = 'minlatency'
MAX_ALL_FLOW = 'maxallflow'
MAX_MIN_FLOW = 'maxminflow'

ALLOCATE_FLOW = 'allocateFlow'
ROUTE_ALL = 'routeAll'
REQ_ALL_LINKS = 'reqAllLinks'
REQ_ALL_NODES = 'reqAllNodes'
REQ_SOME_LINKS = 'reqSomeLinks'
REQ_SOME_NODES = 'reqSomeNodes'
CAP_LINKS = 'capLinks'
CAP_NODES = 'capNodes'

CPLEX = 'cplex'
GUROBI = 'gurobi'
DEFAULT_OPTIMIZER = CPLEX

SELECT_RANDOM = 'random'
SELECT_SHORTEST = 'shortest'

BANDWIDTH = 'bw'
CPU = 'cpu'
MEM = 'mem'
TCAM = 'tcam'

cpdef str xp(TrafficClass trafficClass, Path path, int epoch=0):
    """ Convenience method for formatting a decision variable

    :param trafficClass: the traffic class object, needed for the ID
    :returns: variable name of the form *x_classid_pathindex*
    :rtype: str
    """
    return 'x_{}_{}_{}'.format(trafficClass.ID, path.getID(), epoch)

cpdef str al(TrafficClass trafficClass, int epoch=0):
    """
    Format an allocation variable

    :param trafficClass: the traffic class object
    :return: variable name of the form *a_classid*
    """
    return 'a_{}_{}'.format(trafficClass.ID, epoch)

cpdef str bn(int node):
    """
    Format a binary node variable

    :param node: nodeID
    :return: variable name of the form *binnode_nodeID*
    """
    return 'binnode_{}'.format(node)

cpdef str be(int head, int tail):
    """
    Format a binary edge variable

    :param head: edge head (nodeID)
    :param tail: edge tail (nodeID)
    :return: variable name of the form *binedge_headID_tailID*
    """
    return 'binedge_{}_{}'.format(head, tail)

cpdef str bp(TrafficClass trafficClass, Path path):
    """
    Format a binary path variable

    :param trafficClass: traffic class (for ID)
    :param pathIndex: path index in the list of paths per traffic class
    :return: variable name of the form *binpath_classid_pathindex*
    """
    return 'binpath_{}_{}'.format(trafficClass.ID, path.getID())

cpdef str nl(int node, str resource, int epoch=0):
    """
    Format a node load variable

    :param node: node ID
    :param resource: the resource
    """
    return 'Load_{}_{}_{}'.format(resource, node, epoch)

cpdef str el(tuple link, str resource, int epoch=0):
    """
    Format a link load variable

    :param link:
    :param resource:
    """
    return 'Load_{}_{}_{}'.format(resource, tup2str(link), epoch)

cpdef str nc(int node, str resource, int epoch=0):
    """
    Format a capacity variable

    :param node:
    :param resource:
    """
    return 'Cap_{}_{}_{}'.format(resource, node, epoch)
