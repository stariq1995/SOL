# coding=utf-8
"""
Contains library-wide strings and constants
"""

LINKLOAD_PREFIX = u'LinkLoad'
NODELOAD_PREFIX = u'NodeLoad'
LOAD_PREFIX = u'Load'

MIN_LINK_LOAD = u'minlinkload'
MAX_LINK_SPARE_CAP = u'maxlinkspare'
MIN_NODE_LOAD = u'minnodeload'
MAX_NODE_SPARE_CAP = u'maxnodespare'
MIN_LATENCY = u'minlatency'
MAX_NOT_LATENCY = u'maxnotlatency'
MAX_ALL_FLOW = u'maxallflow'
MAX_MIN_FLOW = u'maxminflow'

ALLOCATE_FLOW = u'allocate_flow'
ROUTE_ALL = u'route_all'
REQ_ALL_LINKS = u'req_all_links'
REQ_ALL_NODES = u'req_all_nodes'
REQ_SOME_LINKS = u'req_some_links'
REQ_SOME_NODES = u'req_some_nodes'
CAP_LINKS = u'capLinks'
CAP_NODES = u'capNodes'

CPLEX = u'cplex'
GUROBI = u'gurobi'
DEFAULT_OPTIMIZER = CPLEX

SELECT_RANDOM = u'random'
SELECT_SHORTEST = u'shortest'
SELECT_ANNEALING = u'sa'

BANDWIDTH = u'bw'
CPU = u'cpu'
MEM = u'mem'
TCAM = u'tcam'
LATENCY = u'Latency'
NOT_LATENCY = u'NotLatency'


HAS_MBOX = u'hasMbox'
SWITCH = u'switch'
SERVICES = u'services'
RESOURCES = u'resources'


FORMAT_GRAPHML = u'graphml'
FORMAT_GML = u'gml'
FORMAT_AUTO = u'auto'

ERR_NO_GUROBI = u'Cannot use Gurobi Python API. Please install Gurobi and gurobipy'