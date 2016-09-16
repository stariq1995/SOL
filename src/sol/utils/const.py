# coding=utf-8
"""
Contains library-wide strings and constants
"""

LINKLOAD_PREFIX = 'LinkLoad'
NODELOAD_PREFIX = 'NodeLoad'
LOAD_PREFIX = 'Load'

MIN_LINK_LOAD = 'minlinkload'
MAX_LINK_SPARE_CAP = 'maxlinkspare'
MIN_NODE_LOAD = 'minnodeload'
MAX_NODE_SPARE_CAP = 'maxnodespare'
MIN_LATENCY = 'minlatency'
MAX_NOT_LATENCY = 'maxnotlatency'
MAX_ALL_FLOW = 'maxallflow'
MAX_MIN_FLOW = 'maxminflow'

ALLOCATE_FLOW = 'allocate_flow'
ROUTE_ALL = 'route_all'
REQ_ALL_LINKS = 'req_all_links'
REQ_ALL_NODES = 'req_all_nodes'
REQ_SOME_LINKS = 'req_some_links'
REQ_SOME_NODES = 'req_some_nodes'
CAP_LINKS = 'capLinks'
CAP_NODES = 'capNodes'

CPLEX = 'cplex'
GUROBI = 'gurobi'
DEFAULT_OPTIMIZER = CPLEX

SELECT_RANDOM = 'random'
SELECT_SHORTEST = 'shortest'
SELECT_ANNEALING = 'sa'

BANDWIDTH = 'bw'
CPU = 'cpu'
MEM = 'mem'
TCAM = 'tcam'
LATENCY = 'Latency'
NOT_LATENCY = 'NotLatency'


HAS_MBOX = 'hasMbox'
SWITCH = 'switch'
SERVICES = 'services'
RESOURCES = 'resources'


FORMAT_GRAPHML = 'graphml'
FORMAT_GML = 'gml'
FORMAT_AUTO = 'auto'