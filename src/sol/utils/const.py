# coding=utf-8
"""
Contains library-wide strings and constants
"""
from enum import Enum, IntEnum

# LINKLOAD_PREFIX = u'LinkLoad'
# NODELOAD_PREFIX = u'NodeLoad'
# LOAD_PREFIX = u'Load'
MIN_LOAD_PREFIX = 'MINLOAD'

# OBJ_MAX_LINK_SPARE_CAP = u'maxlinkspare'
# OBJ_MAX_NODE_SPARE_CAP = u'maxnodespare'
# OBJ_MAX_NOT_LATENCY = u'maxnotlatency'
# OBJ_MAX_LINK_SPARE_CAP = u'maxlinkspare'
# MIN_LINK_LOAD = u'minlinkload'
# MIN_NODE_LOAD = u'minnodeload'
# MAX_NODE_SPARE_CAP = u'maxnodespare'
# OBJ_MIN_LATENCY = u'minlatency'
# MAX_NOT_LATENCY = u'maxnotlatency'
# OBJ_MAX_ALL_FLOW = u'maxallflow'
# MAX_MIN_FLOW = u'maxminflow'
# THE_OBJECTIVE = u'theobjective'


class Objective(Enum):
    # OBJ_MAX_LINK_SPARE_CAP = u'maxlinkspare'
    # OBJ_MAX_NODE_SPARE_CAP = u'maxnodespare'
    # OBJ_MAX_NOT_LATENCY = u'maxnotlatency'
    # OBJ_MAX_LINK_SPARE_CAP = u'maxlinkspare'
    MIN_LINK_LOAD = u'minlinkload'
    MIN_NODE_LOAD = u'minnodeload'
    # MAX_NODE_SPARE_CAP = u'maxnodespare'
    MIN_LATENCY = u'minlatency'
    # MAX_NOT_LATENCY = u'maxnotlatency'
    MAX_ALL_FLOW = u'maxallflow'
    # MAX_MIN_FLOW = u'maxminflow'
    THE_OBJECTIVE = u'theobjective'


class Resource(Enum):
    """
    Pre-defined resource names
    """
    BANDWIDTH = u'bw'
    CPU = u'cpu'
    MEM = u'mem'
    TCAM = u'tcam'
    LATENCY = u'Latency'


class BinType(Enum):
    """
    Type of binary variable
    """
    BIN_NODE = u'node'
    BIN_EDGE = u'edge'
    BIN_LINK = BIN_EDGE
    BIN_PATH = u'path'


class ResConsumeMode(IntEnum):
    PER_FLOW = 1
    PER_PATH = 2


class NodeConsumeMode(IntEnum):
    """
    Resource consumption mode for nodes in a path.
    """
    ALL = 1  # All nodes with the resource
    MBOXES = 2  # Only middleboxes consume resources


class EpochComposition(Enum):
    AVG = u'sum'
    WORST = u'worst'


ALLOCATE_FLOW = u'allocate_flow'
ROUTE_ALL = u'route_all'
REQ_ALL_LINKS = u'req_all_links'
REQ_ALL_NODES = u'req_all_nodes'
REQ_SOME_LINKS = u'req_some_links'
REQ_SOME_NODES = u'req_some_nodes'
CAP_LINKS = u'caplinks'
CAP_NODES = u'capnodes'

class ComposeMode(Enum):
    WEIGHTED = u'weighted'
    UTILITARIAN = WEIGHTED
    PROPFAIR = u'propfair'
    MAXMIN = u'maxmin'

# CPLEX = u'cplex'
# GUROBI = u'gurobi'
# DEFAULT_OPTIMIZER = GUROBI
NODES = 'nodes'
LINKS = 'links'

SELECT_RANDOM = u'random'
SELECT_SHORTEST = u'shortest'
SELECT_ANNEALING = u'sa'

# Topology fields
HAS_MBOX = u'hasMbox'
SWITCH = u'switch'
SERVICES = u'services'
RESOURCES = u'resources'

# Fields specific to FatTree topologies
CORE_LAYER = u'core'
EDGE_LAYER = u'edge'
AGG_LAYER = u'aggregation'

# Supported formats of topology files
FORMAT_GRAPHML = u'graphml'
FORMAT_GML = u'gml'
FORMAT_AUTO = u'auto'

# Error/warning strings
ERR_NO_GUROBI = u'Cannot use Gurobi Python API. Please install Gurobi and ' \
                u'gurobipy'
ERR_FMT = u'Given format is not supported'
ERR_NO_PATH = u'No paths between nodes {} and {}'
ERR_EPOCH_MISMATCH = u'Number of epochs insosistent across traffic classes'
ERR_BAD_CAPVAL = u'Bad reousrce cap value. Must be between 0 and 1'
ERR_UNKNOWN_MODE = u'Uknown %s mode: %s'
ERR_UNKNOWN_TYPE = u'Uknonw %s type: %s'
ERR_ODD_ARITY = u'-arity of a FatTree topology must be even'
ERR_OP_NOT_SUPP = u'Operation not supported'
WARN_NO_PATH_ID = u'No ID given to Path constructor, ' \
                  u'generating a random path ID'
