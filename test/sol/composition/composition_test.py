# coding=utf-8
from __future__ import print_function

import itertools
import pytest
import tmgen

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
from sol.utils.const import BANDWIDTH, Objective, Constraint, Fairness, EpochComposition

# a sensitivity epsilon for objective function presicion
EPSILON = 1e-5


@pytest.fixture(params=[3, 4, 5], scope='module')
def topo(request):
    n = 5
    t = complete_topology(request.param)
    for l in t.links():
        t.set_resource(l, BANDWIDTH, n * (n - 1))
    return t


@pytest.fixture(scope='module')
def pptc(topo):
    # generate a dummy TM and traffic classes
    tm = tmgen.exact_tm(topo.num_nodes(), 1)
    tc = traffic_classes(tm, {u'all': 1}, as_dict=False)
    # generate all possibe paths
    res = generate_paths_tc(topo, tc, null_predicate, 10, max_paths=float('inf'))
    return res


@pytest.fixture(scope='module')
def netconf(topo):
    caps = NetworkCaps(topo)
    caps.add_cap(BANDWIDTH, cap=1)
    return NetworkConfig(caps)


@pytest.mark.parametrize("fairness,epochmode", itertools.product(list(Fairness), list(EpochComposition)))
def test_compose_latency_maxflow(topo, pptc, netconf, fairness, epochmode):
    """
    Test the composition of a maxflow and minlatency app on a complete topology
    :return: 
    """
    cost_func = CostFuncFactory.from_number(1)
    mf_app = AppBuilder().name('mf') \
        .pptc(pptc) \
        .objective(Objective.MAX_FLOW) \
        .add_resource(BANDWIDTH, cost_func, 'links') \
        .build()

    latency_app = AppBuilder().name('minlatency') \
        .pptc(pptc) \
        .add_constr(Constraint.ROUTE_ALL)\
        .objective(Objective.MIN_LATENCY) \
        .add_resource(BANDWIDTH, cost_func, 'links') \
        .build()

    opt = compose_apps([mf_app, latency_app], topo, netconf, fairness=fairness,
                       epoch_mode=epochmode)
    opt.solve()
    opt.write('debug')
    assert opt.is_solved()
    opt.write_solution('debug')

    # max flow objective
    mfo = opt.get_solved_objective(mf_app)
    # latency objective, 1- because max/min flip
    lato = 1 - opt.get_solved_objective(latency_app)
    assert mfo == 1 or abs(mfo - 1) < EPSILON
    # We should be able to get all traffic routed on shortest paths
    # Which means the latency should be
    n = topo.num_nodes()
    expected = (n - 1) / n
    assert lato == expected or abs(lato - expected) < EPSILON


@pytest.mark.skip()
@pytest.mark.parametrize("fairness", [Fairness.WEIGHTED, Fairness.MAXMIN, Fairness.PROPFAIR])
def test_compose_te_latency(topo, pptc, netconf, fairness):
    cost_func = CostFuncFactory.from_number(.5)
    te_app = AppBuilder().name('te') \
        .pptc(pptc) \
        .add_constr(Constraint.ROUTE_ALL) \
        .objective(Objective.MIN_LINK_LOAD, BANDWIDTH) \
        .add_resource(BANDWIDTH, cost_func, 'links') \
        .build()

    latency_app = AppBuilder().name('minlatency') \
        .pptc(pptc) \
        .objective(Objective.MIN_LATENCY) \
        .add_resource(BANDWIDTH, cost_func, 'links') \
        .build()

    opt = compose_apps([te_app, latency_app], topo, netconf, fairness=fairness)
    opt.solve()
    assert opt.is_solved()

    # te objective
    teo = opt.get_solved_objective(te_app)
    assert teo == .5 or abs(teo - .5) < EPSILON
    # latency objective
    lato = opt.get_solved_objective(latency_app)
    assert lato == 1.0 / topo.num_nodes() or abs(lato - 1.0 / topo.num_nodes()) < EPSILON


@pytest.mark.skip()
def test_annealing_selection(topo, pptc, netconf):
    cost_func = CostFuncFactory.from_number(1)
    mf_app = AppBuilder().name('mf') \
        .pptc(pptc) \
        .objective(Objective.MAX_FLOW) \
        .add_resource(BANDWIDTH, cost_func, 'links') \
        .build()

    latency_app = AppBuilder().name('minlatency') \
        .pptc(pptc) \
        .objective(Objective.MIN_LATENCY) \
        .add_resource(BANDWIDTH, cost_func, 'links') \
        .build()

    opt = select_sa([mf_app, latency_app], topo, netconf)
    opt.solve()
    assert opt.is_solved()
    # We should be able to get all traffic routed. Which means
    # the latency should be a 1/n

    # max flow objective
    mfo = opt.get_solved_objective(mf_app)
    assert mfo == 1 or abs(mfo - 1) < EPSILON
    # latency objective
    lato = opt.get_solved_objective(latency_app)
    assert lato == 1.0 / topo.num_nodes() or abs(lato - 1.0 / topo.num_nodes()) < EPSILON
