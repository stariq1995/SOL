# coding=utf-8
from __future__ import print_function

import itertools
import pytest
import tmgen
from hypothesis import given
from hypothesis import strategies as st
from numpy import linspace

from sol import AppBuilder
from sol import NetworkCaps
from sol import NetworkConfig
from sol.opt.composer import compose_apps
from sol.opt.funcs import CostFuncFactory
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.path.select import select_sa
from sol.topology.generators import complete_topology
from sol.topology.provisioning import traffic_classes
from sol.utils.const import BANDWIDTH, Objective, Constraint, Fairness, EpochComposition, LINKS

# a sensitivity epsilon for objective function presicion
EPSILON = 1e-5


@pytest.fixture(params=[3])
def topo(request):
    n = request.param
    t = complete_topology(n)
    for l in t.links():
        t.set_resource(l, BANDWIDTH, n * (n - 1))
    return t


@pytest.fixture()
def pptc(topo):
    # generate a dummy TM and traffic classes
    tm = tmgen.exact_tm(topo.num_nodes(), 1)
    tc = traffic_classes(tm, {u'all': 1}, as_dict=False)
    # generate all possibe paths
    res = generate_paths_tc(topo, tc, null_predicate, 10, max_paths=float('inf'))
    return res


@pytest.fixture()
def netconf(topo):
    caps = NetworkCaps(topo)
    caps.add_cap(BANDWIDTH, cap=1)
    return NetworkConfig(caps)


# @pytest.mark.parametrize("fairness,epochmode", itertools.product(list(Fairness), list(EpochComposition)))
@pytest.mark.parametrize("fairness,epochmode", itertools.product([Fairness.WEIGHTED], list(EpochComposition)))
def test_compose_latency_maxflow(topo, pptc, netconf, fairness, epochmode):
    """
    Test the composition of a maxflow and minlatency app on a complete topology
    :return: 
    """
    cost_func = CostFuncFactory.from_number(1)
    mf_app = AppBuilder().name('mf') \
        .pptc(pptc) \
        .objective(Objective.MAX_FLOW) \
        .add_resource(BANDWIDTH, LINKS, 1) \
        .build()

    latency_app = AppBuilder().name('minlatency') \
        .pptc(pptc) \
        .add_constr(Constraint.ROUTE_ALL) \
        .objective(Objective.MIN_LATENCY) \
        .add_resource(BANDWIDTH, LINKS, 1) \
        .build()

    opt = compose_apps([mf_app, latency_app], topo, netconf, fairness=fairness,
                       epoch_mode=epochmode)
    opt.solve()
    if fairness == Fairness.PROPFAIR:
        opt.write('debug')
    assert opt.is_solved()

    # max flow objective
    mfo = opt.get_solved_objective(mf_app)[0]
    # latency objective, 1- because max/min flip
    lato = 1 - opt.get_solved_objective(latency_app)[0]
    assert mfo == 1 or abs(mfo - 1) < EPSILON
    # We should be able to get all traffic routed on shortest paths
    # Which means the latency should be
    n = topo.num_nodes()
    expected = (n - 1) / n
    assert lato == expected or abs(lato - expected) < EPSILON


@pytest.mark.parametrize("fairness,epochmode,cost", itertools.product([Fairness.WEIGHTED], list(EpochComposition),
                                                                      linspace(.01, 1, 5)))
def test_compose_te_latency(topo, pptc, netconf, fairness, epochmode, cost):
    te_app = AppBuilder().name('te') \
        .pptc(pptc) \
        .add_constr(Constraint.ROUTE_ALL) \
        .objective(Objective.MIN_LINK_LOAD, BANDWIDTH) \
        .add_resource(BANDWIDTH, LINKS, cost) \
        .build()

    latency_app = AppBuilder().name('minlatency') \
        .pptc(pptc) \
        .objective(Objective.MIN_LATENCY) \
        .add_resource(BANDWIDTH, LINKS, cost) \
        .build()

    opt = compose_apps([te_app, latency_app], topo, netconf, fairness=fairness,
                       epoch_mode=epochmode)
    opt.solve()
    opt.write('debug_te_lat')
    assert opt.is_solved()
    opt.write_solution('debug_te_lat')

    # compute expected values
    n = topo.num_nodes()
    cap = n * (n-1)

    # te objective
    teo = opt.get_solved_objective(te_app)[0]
    assert 1-teo == cost/cap or abs(1-teo - cost/cap) < EPSILON
    # latency objective
    lato = opt.get_solved_objective(latency_app)[0]
    assert lato == 1.0 / topo.num_nodes() or abs(lato - 1.0 / topo.num_nodes()) < EPSILON


# @pytest.mark.skip()
# def test_annealing_selection(topo, pptc, netconf):
#     cost_func = CostFuncFactory.from_number(1)
#     mf_app = AppBuilder().name('mf') \
#         .pptc(pptc) \
#         .objective(Objective.MAX_FLOW) \
#         .add_resource(BANDWIDTH, LINKS, 1) \
#         .build()
#
#     latency_app = AppBuilder().name('minlatency') \
#         .pptc(pptc) \
#         .objective(Objective.MIN_LATENCY) \
#         .add_resource(BANDWIDTH, LINKS, 1) \
#         .build()
#
#     opt = select_sa([mf_app, latency_app], topo, netconf)
#     opt.solve()
#     assert opt.is_solved()
#     # We should be able to get all traffic routed. Which means
#     # the latency should be a 1/n
#
#     # max flow objective
#     mfo = opt.get_solved_objective(mf_app)[0]
#     assert mfo == 1 or abs(mfo - 1) < EPSILON
#     # latency objective
#     lato = opt.get_solved_objective(latency_app)[0]
#     assert lato == 1.0 / topo.num_nodes() or abs(lato - 1.0 / topo.num_nodes()) < EPSILON
