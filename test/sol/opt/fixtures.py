# coding=utf-8
from random import sample

from sol.opt.app import App
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.topology.generators import complete_topology
from sol.topology.traffic import TrafficClass
from sol.utils.const import ALLOCATE_FLOW, ROUTE_ALL, OBJ_MIN_LATENCY, \
    RES_BANDWIDTH, OBJ_MAX_ALL_FLOW


def mock_topo():
    """
    Returns a complete topology with 5 nodes. No middleboxes or link capacities
    are configured

    :return: a new :py:class:`~sol.topology.topologynx.Topology`
    """
    return complete_topology(5)


def _get_pptc(topo, appconfig):
    # Generate a single traffic class:
    nodes = sample(list(topo.nodes()), 2)
    tcs = [TrafficClass(1, u'classname', nodes[0], nodes[1])]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, appconfig['predicate'],
                             cutoff=100)
    return pptc


def mock_min_latency_app(topo):
    """
    Return a simple mock min latency app with a single traffic class.
    The traffic class will be between two randomly chosen nodes
    """
    # Application configuration
    appconfig = {
        'name': u'mockminLatencyApp',
        'constraints': [ALLOCATE_FLOW, ROUTE_ALL],
        'obj': OBJ_MIN_LATENCY,
        'predicate': null_predicate,
        'resource_cost': {RES_BANDWIDTH: 100}
    }

    # Create an application based on our config
    app = App(_get_pptc(topo, appconfig), **appconfig)
    return app


def mock_max_flow_app(topo):
    """
    Return a simple mock maxflow app with a single traffic class
    The traffic class will be between two randomly chosen nodes

    :return:
    """
    appconfig = {
        'name': u'mockmaxflowapp',
        'constraints': [ALLOCATE_FLOW],
        'obj': OBJ_MAX_ALL_FLOW,
        'predicate': null_predicate,
        'resource_cost': {RES_BANDWIDTH: 100}
    }

    # Create an application based on our config
    app = App(_get_pptc(topo, appconfig), **appconfig)
    return app

