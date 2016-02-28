from sol.utils.pythonHelper import tup2str

LINKLOAD_PREFIX = 'LinkLoad'
LOAD_PREFIX = 'Load'

MIN_LINK_LOAD = 'minlinkload'
MIN_NODE_LOAD = 'minnodeload'
MIN_LATENCY = 'minlatency'
MAX_ALL_FLOW = 'maxallflow'
MAX_MIN_FLOW = 'maxminflow'
MIN_ROUTING_COST = 'minroutingcost'

ALLOCATE_FLOW = 'allocateFlow'
ROUTE_ALL = 'routeAll'
REQ_ALL_LINKS = 'reqAllLinks'
REQ_ALL_NODES = 'reqAllNodes'
CAP_LINKS = 'capLinks'
CAP_NODES = 'capNodes'
#TODO: expand available constraint name constants


CPLEX = 'cplex'
GUROBI = 'gurobi'
DEFAULT_OPTIMIZER = CPLEX

SELECT_RANDOM = 'random'
SELECT_SHORTEST = 'shortest'

RES_COMPOSE_MAX = 1
RES_COMPOSE_SUM = 2
RES_COMPOSE_CONFLICT = 3


SHARE_PROPORTIONAL_VOLUME = 1
SHARE_EQUAL = 2
SHARE_NUM_APPS = 4


def xp(trafficClass, path):
    """ Convenience method for formatting a decision variable

    :param trafficClass: the traffic class object, needed for the ID
    :param pathIndex: index of the path in the list of paths per traffic class
    :returns: variable name of the form *x_classid_pathindex*
    :rtype: str
    """
    return 'x_{}_{}'.format(trafficClass.ID, path.getID())


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


def bp(trafficClass, path):
    """
    Format a binary path variable

    :param trafficClass: traffic class (for ID)
    :param pathIndex: path index in the list of paths per traffic class
    :return: variable name of the form *binpath_classid_pathindex*
    """
    return 'binpath_{}_{}'.format(trafficClass.ID, path.getID())


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
