# coding=utf-8
from itertools import product

import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy import array

from sol import NetworkCaps
from sol import NetworkConfig
from sol.opt.app import App
from sol.opt.funcs import CostFuncFactory
from sol.opt.quickstart import from_app
from sol.path.generate import generate_paths_tc, use_mbox_modifier
from sol.path.predicates import null_predicate, has_mbox_predicate
from sol.topology.generators import complete_topology
from sol.topology.traffic import TrafficClass
from sol.utils.const import *


# When comparing objective functions, use this as the precision


def test_shortest_path():
    """ Check that we can correctly implement shortest path routing """
    # Generate a topology:
    topo = complete_topology(5)

    # Generate a single traffic class:
    # TrafficClass (id, name, source node, destination node)
    tcs = [TrafficClass(0, u'classname', 0, 2)]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, null_predicate, cutoff=100)
    # Application configuration
    appconfig = {
        'name': u'minLatencyApp',
        'constraints': [(Constraint.ROUTE_ALL, (pptc.tcs(),), {})],
        'obj': (Objective.MIN_LATENCY, (), {}),
        'resource_cost': {}
    }

    # Create an application based on our config
    app = App(pptc, **appconfig)

    # Create and solve an optimization based on the app
    # No link capacities will just result in a single shortest path
    opt = from_app(topo, app, NetworkConfig(None))
    opt.solve()
    assert opt.is_solved()

    paths = opt.get_paths()
    for pi, p in enumerate(paths.paths(tcs[0])):
        if list(p.nodes()) == [0, 2]:
            assert p.flow_fraction() == 1
        else:
            assert p.flow_fraction() == 0

    # norm factor for latency is diameter * n^2
    norm = topo.diameter() * 25
    # the objective is 1-normalized latency, and latency is 1.
    # because 1 path with flow fraction of 1.
    solution = opt.get_solved_objective(app)[0]
    assert solution == 1 - 1 / norm or abs(solution - 1 - 1 / norm) <= EPSILON
    solution = opt.get_solved_objective()
    assert solution == 1 - 1 / norm or abs(solution - 1 - 1 / norm) <= EPSILON


@given(st.floats(1e-3, 1))
def test_maxflow(cap):
    """ Check that maxflow works correctly, for a single traffic class """
    # Generate a topology:
    topo = complete_topology(4)
    for link in topo.links():
        topo.set_resource(link, BANDWIDTH, 1)
    tcs = [TrafficClass(0, u'classname', 0, 2, array([3]))]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, null_predicate, cutoff=100)

    appconfig = {
        'name': u'mf',
        'constraints': [],
        'obj': (Objective.MAX_FLOW, (), {}),
        'resource_cost': {BANDWIDTH: (LINKS, 1, None)}
    }
    app = App(pptc, **appconfig)
    caps = NetworkCaps(topo)
    caps.add_cap(BANDWIDTH, cap=cap)
    opt = from_app(topo, app, NetworkConfig(caps))
    opt.solve()
    assert opt.is_solved()
    # Ensure that both app objective and global objective are the same
    # Also, use abs(actual - exprected) because floating point errors
    solution = opt.get_solved_objective(app)[0]
    assert solution == cap or abs(solution - cap) <= EPSILON
    solution = opt.get_solved_objective()
    assert solution == cap or abs(solution - cap) <= EPSILON


@given(st.floats(0, 1))
def test_maxflow_inapp_caps(cap):
    """Text maxflow, but use the CAP constraint instead of global network caps"""
    # Generate a topology:
    topo = complete_topology(4)
    for link in topo.links():
        topo.set_resource(link, BANDWIDTH, 1)
    tcs = [TrafficClass(0, u'classname', 0, 2, array([3]))]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, null_predicate, cutoff=100)
    caps = {link: cap for link in topo.links()}
    appconfig = {
        'name': u'mf',
        'constraints': [(Constraint.CAP_LINKS, (BANDWIDTH, caps), {})],
        'obj': (Objective.MAX_FLOW, (), {}),
        'resource_cost': {BANDWIDTH: (LINKS, 1, None)}
    }
    app = App(pptc, **appconfig)
    opt = from_app(topo, app, NetworkConfig())
    opt.solve()
    assert opt.is_solved()
    # Ensure that both app objective and global objective are the same
    # Also, use abs(actual - exprected) because floating point errors
    solution = opt.get_solved_objective(app)[0]
    assert solution == cap or abs(solution - cap) <= EPSILON
    solution = opt.get_solved_objective()
    assert solution == cap or abs(solution - cap) <= EPSILON


def test_min_latency_app():
    """Test a single min latency app"""
    topo = complete_topology(4)
    for link in topo.links():
        topo.set_resource(link, BANDWIDTH, 1)
    tcs = [TrafficClass(0, u'classname', 0, 2, array([1]))]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, null_predicate, cutoff=100)
    appconfig = {
        'name': u'te',
        'constraints': [(Constraint.ROUTE_ALL, (), {})],
        'obj': (Objective.MIN_LATENCY, (), {}),
        'resource_cost': {BANDWIDTH: (LINKS, 1, None)}
    }
    app = App(pptc, **appconfig)
    caps = NetworkCaps(topo)
    caps.add_cap(BANDWIDTH, cap=1)
    opt = from_app(topo, app, NetworkConfig(caps))
    opt.solve()
    assert opt.is_solved()

    # norm factor for latency is diameter * n^2
    norm = topo.diameter() * 16
    # the objective is 1-normalized latency, and latency is 1.
    # because 1 path with flow fraction of 1.
    solution = opt.get_solved_objective(app)[0]
    assert solution == 1 - 1 / norm or abs(solution - (1 - 1 / norm)) <= EPSILON
    solution = opt.get_solved_objective()
    assert solution == 1 - 1 / norm or abs(solution - (1 - 1 / norm)) <= EPSILON


def test_te_app():
    """ Test a single traffic engineering app"""
    topo = complete_topology(4)
    for link in topo.links():
        topo.set_resource(link, BANDWIDTH, 1)
    tcs = [TrafficClass(0, u'classname', 0, 2, array([1]))]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, null_predicate, cutoff=100)
    appconfig = {
        'name': u'te',
        'constraints': [(Constraint.ROUTE_ALL, (), {})],
        'obj': (Objective.MIN_LINK_LOAD, (BANDWIDTH,), {}),
        'resource_cost': {BANDWIDTH: (LINKS, 1, None)}
    }
    app = App(pptc, **appconfig)
    caps = NetworkCaps(topo)
    caps.add_cap(BANDWIDTH, cap=1)
    opt = from_app(topo, app, NetworkConfig(caps))
    opt.solve()
    assert opt.is_solved()
    # THE solution is 1-objective because of the maximization flip
    solution = 1 - opt.get_solved_objective(app)[0]
    # Use abs(actual - exprected) because floating point errors
    assert solution == .333333 or abs(solution - .33333) <= EPSILON
    solution = 1 - opt.get_solved_objective()
    assert solution == .333333 or abs(solution - .33333) <= EPSILON


def test_mbox_load_balancing():
    """Test the middlebox loadbalancing"""

    topo = complete_topology(4)
    for n in topo.nodes():
        topo.set_resource(n, CPU, 1)
        topo.set_mbox(n)
    tcs = [TrafficClass(0, u'classname', 0, 2, array([1]))]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, has_mbox_predicate, modify_func=use_mbox_modifier, cutoff=100)
    appconfig = {
        'name': u'mb_lb',
        'constraints': [(Constraint.ROUTE_ALL, (), {})],
        'obj': (Objective.MIN_NODE_LOAD, (CPU,), {}),
        'resource_cost': {CPU: (MBOXES, 1, None)}
    }
    app = App(pptc, **appconfig)
    caps = NetworkCaps(topo)
    caps.add_cap(CPU, cap=1)
    opt = from_app(topo, app, NetworkConfig(caps))
    opt.solve()
    assert opt.is_solved()
    # THE solution is 1-objective because of the maximization flip
    solution = 1 - opt.get_solved_objective(app)[0]
    # Use abs(actual - exprected) because floating point errors
    assert solution == .25 or abs(solution - .25) <= EPSILON
    solution = 1 - opt.get_solved_objective()
    assert solution == .25 or abs(solution - .25) <= EPSILON


def test_mbox_load_balancing_all_tcs():
    """Test the middlebox loadbalancing"""

    topo = complete_topology(4)
    for n in topo.nodes():
        topo.set_resource(n, CPU, 1)
        topo.set_mbox(n)
    tcs = [TrafficClass(0, u'classname', s, t, array([1])) for (s, t) in product(topo.nodes(), repeat=2)]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, has_mbox_predicate, modify_func=use_mbox_modifier, cutoff=100)
    appconfig = {
        'name': u'mb_lb',
        'constraints': [(Constraint.ROUTE_ALL, (), {})],
        'obj': (Objective.MIN_NODE_LOAD, (CPU,), {}),
        'resource_cost': {CPU: (MBOXES, 1, None)}
    }
    app = App(pptc, **appconfig)
    caps = NetworkCaps(topo)
    caps.add_cap(CPU, cap=1)
    opt = from_app(topo, app, NetworkConfig(caps))
    opt.solve()
    assert opt.is_solved()
    # THE solution is 1-objective because of the maximization flip
    solution = 1 - opt.get_solved_objective(app)[0]
    # Use abs(actual - exprected) because floating point errors
    assert solution == 1 or abs(solution - 1) <= EPSILON
    solution = 1 - opt.get_solved_objective()
    assert solution == 1 or abs(solution - 1) <= EPSILON


@pytest.mark.skip()
def test_fixed_paths():
    pass
    # TODO: bring back fixed paths test
