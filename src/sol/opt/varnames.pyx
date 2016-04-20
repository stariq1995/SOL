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

cpdef xp(TrafficClass trafficClass, Path path):
    """ Convenience method for formatting a decision variable

    :param trafficClass: the traffic class object, needed for the ID
    :returns: variable name of the form *x_classid_pathindex*
    :rtype: str
    """
    return 'x_{}_{}'.format(trafficClass.ID, path.getID())

cpdef al(TrafficClass trafficClass):
    """
    Format an allocation variable

    :param trafficClass: the traffic class object
    :return: variable name of the form *a_classid*
    """
    return 'a_{}'.format(trafficClass.ID)

cpdef bn(int node):
    """
    Format a binary node variable

    :param node: nodeID
    :return: variable name of the form *binnode_nodeID*
    """
    return 'binnode_{}'.format(node)

cpdef be(int head, int tail):
    """
    Format a binary edge variable

    :param head: edge head (nodeID)
    :param tail: edge tail (nodeID)
    :return: variable name of the form *binedge_headID_tailID*
    """
    return 'binedge_{}_{}'.format(head, tail)

cpdef bp(TrafficClass trafficClass, Path path):
    """
    Format a binary path variable

    :param trafficClass: traffic class (for ID)
    :param pathIndex: path index in the list of paths per traffic class
    :return: variable name of the form *binpath_classid_pathindex*
    """
    return 'binpath_{}_{}'.format(trafficClass.ID, path.getID())

cpdef nl(int node, str resource):
    """
    Format a node load variable

    :param node: node ID
    :param resource: the resource
    """
    return 'Load_{}_{}'.format(resource, node)

cpdef el(tuple link, str resource):
    """
    Format a link load variable

    :param link:
    :param resource:
    """
    return 'Load_{}_{}'.format(resource, tup2str(link))

cpdef nc(int node, str resource):
    """
    Format a capacity variable

    :param node:
    :param resource:
    """
    return 'Cap_{}_{}'.format(resource, node)
