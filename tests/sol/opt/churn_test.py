import logging
import os
import json
from collections import defaultdict

import numpy as np
import networkx as nx

from sol.opt.app import App
from sol import (AppBuilder, NetworkCaps, NetworkConfig, Topology,
                 TrafficClass, from_app, from_app_weighted)
from sol.topology.generators import complete_topology
from sol.path.generate import generate_paths_tc
from sol.utils.const import Constraint, Objective, EpochComposition, Fairness
from sol.opt.composer import compose_apps



# def topo(n):
#     t = complete_topology(n)
#     for l in t.links():
#         t.set_resource(l, 'BANDWIDTH', n * (n - 1) * 100)
#     return t

def create_test_topo(n, b_cap):
    g = nx.DiGraph()

    for i in range(1, n):
        g.add_edge(0, i)
    
    for i in range(1, n):
        g.add_edge(i, n)

    print(g.edges)
    t = Topology("Sanity Check Topology", graph=g)

    for l in t.links():
        t.set_resource(l, 'bandwidth', b_cap)

    return t

def create_tcs(n, epochs, load):
    tcs = {}
    for i in range(1, n):
        tcs[(i, n)] = [0 if t < i else load for t in range(epochs)]

    tcs[(0, n)] = [5*load for _ in range(epochs)]
    return tcs

def test_min_alloc():
    """ Check that we can correctly implement shortest path routing """
    # Generate a topology:

    topo = complete_topology(3)
    for l in topo.links():
        # topo.set_resource(l, 'bandwidth', 3 * (3 - 1) * 100)
        topo.set_resource(l, 'bandwidth', 50)

    # Generate a single traffic class:
    # TrafficClass (id, name, source node, destination node)
    epochs = 3
    vols = [4, 8, 8]
    tcs = [TrafficClass(0, u'classname', 0, 2, np.array(vols))]
    # Generate all paths for this traffic class
    
    pptc = generate_paths_tc(topo, tcs, cutoff=100)


    curr = np.random.rand(1, 2)
    # curr = None
    curr_vols = np.zeros(shape=(1, 1), dtype=float)
    for tc in pptc.tcs():
        curr_vols[tc.ID] = 0
    # curr_vols = None

    app = AppBuilder().name('te') \
        .pptc(pptc)\
        .add_constr(Constraint.ROUTE_ALL)\
        .add_constr(Constraint.MIN_ALLOCATION, 5.0)\
        .objective(Objective.MIN_STABLE_LOAD, resource="bandwidth", weights=[1, 0], current_allocation=curr, current_vols=curr_vols, normalizer=100)\
        .add_resource(name='bandwidth', applyto='links', cost_val=1).build()

    caps = NetworkCaps(topo)
    caps.add_cap('bandwidth', cap=1)
    nconfig = NetworkConfig(caps)
    

    opt = from_app_weighted(topo, app, nconfig, [3, 2, 1])

    print("Printing model")
    opt.write(CUR_DIR + "model.lp")
    

    # Create and solve an optimization based on the app
    # No link capacities will just result in a single shortest path
    opt.solve()
    print(opt.opt.status)
    # opt.opt.Params.dualreductions = 0.0
    # opt.solve()
    # print(opt.opt.status)
    assert opt.is_solved()
    print(opt.get_solved_objective(app))

    print(opt.get_var_values())
    churn_optvals = [opt.opt.getVarByName('churn_{}_{}'.format(app.name, e)).x for e in range(epochs)]
    print("churn vals:", churn_optvals)
    
    load_optvals = [opt.opt.getVarByName('load_{}_{}'.format(app.name, e)).x for e in range(epochs)]
    print("load vals:", load_optvals)

    

    print("Paths taken by 0->5")
    print(opt.get_paths(0).paths(tcs[-1]))
    print(opt.get_paths(1).paths(tcs[-1]))
    print(opt.get_paths(2).paths(tcs[-1]))
    


    print(opt.volumes)


def test_stable():
    """ Check that we can correctly implement shortest path routing """
    # Generate a topology:

    topo = create_test_topo(5, 100)
    epochs = 4
    tf = create_tcs(5, epochs, 10)
    # topo = complete_topology(3)
    # for l in topo.links():
    #     # topo.set_resource(l, 'bandwidth', 3 * (3 - 1) * 100)
    #     topo.set_resource(l, 'bandwidth', 50)

    # # Generate a single traffic class:
    # # TrafficClass (id, name, source node, destination node)
    # vols = [20, 30, 40]
    # tcs = [TrafficClass(0, u'classname', 0, 2, np.array(vols))]
    # # Generate all paths for this traffic class
    tcs = []
    for i, ((s, d), vol) in enumerate(tf.items()):
        tcs.append(TrafficClass(i, u'%d->%d' % (s, d), s, d, np.array(vol)))
    print(tcs)
    pptc = generate_paths_tc(topo, tcs, cutoff=100)
    # Application configuration
    # appconfig = {
    #     'name': u'minChurnApp',
    #     'constraints': [(Constraint.ROUTE_ALL, (pptc.tcs(),), {})],
    #     'obj': (Objective.MIN_CHURN, (), {}),
    #     'resource_cost': {}
    # }


    # # Create an application based on our config
    # app = App(pptc, **appconfig)
    # print(app.name)

    curr = np.random.rand(5, 4)
    # curr = None
    curr_vols = np.zeros(shape=(5, 1), dtype=float)
    for tc in pptc.tcs():
        curr_vols[tc.ID] = tc.ID * 5
    # curr_vols = None

    app = AppBuilder().name('te') \
        .pptc(pptc)\
        .add_constr(Constraint.ROUTE_ALL)\
        .objective(Objective.MIN_STABLE_LOAD_SUM, resource="bandwidth", weights=[1, 0], current_allocation=curr, current_vols=curr_vols, normalizer=100)\
        .add_resource(name='bandwidth', applyto='links', cost_val=1).build()

    caps = NetworkCaps(topo)
    caps.add_cap('bandwidth', cap=1)
    nconfig = NetworkConfig(caps)
    

    opt = from_app_weighted(topo, app, nconfig, [3, 2, 1])
    for tc in pptc.tcs():
        opt.cap_num_paths(max_paths=2, pptc=generate_paths_tc(topo, [tcs[tc.ID]], cutoff=100))
    # opt.cap_num_paths(max_paths=4)

    print("Printing model")
    opt.write(CUR_DIR + "model.lp")
    

    # Create and solve an optimization based on the app
    # No link capacities will just result in a single shortest path
    opt.solve()
    print(opt.opt.status)
    # opt.opt.Params.dualreductions = 0.0
    # opt.solve()
    # print(opt.opt.status)
    assert opt.is_solved()
    print(opt.get_solved_objective(app))
    # print(opt.get_solved_objective(te_app))
    # print(opt.get_solved_objective(churn_app))

    print(opt.get_var_values())
    churn_optvals = [opt.opt.getVarByName('churn_{}_{}'.format(app.name, e)).x for e in range(epochs)]
    print("churn vals:", churn_optvals)
    
    load_optvals = [opt.opt.getVarByName('load_{}_{}'.format(app.name, e)).x for e in range(epochs)]
    print("load vals:", load_optvals)

    # print(opt.get_xps()[0, 0, :])
    # print(opt.get_xps()[0, 1, :])

    # print(opt.get_paths(0))
    # print(opt.get_paths(1))
    # print(opt.get_paths(2))
    # print(opt.get_paths(3))
    # print(opt.get_paths(4))


    print("Paths taken by 0->5")
    print(opt.get_paths(0).paths(tcs[-1]))
    print(opt.get_paths(1).paths(tcs[-1]))
    print(opt.get_paths(2).paths(tcs[-1]))
    print(opt.get_paths(3).paths(tcs[-1]))

    print("Paths taken by 3->5")

    print(opt.get_paths(0).paths(tcs[2]))
    print(opt.get_paths(1).paths(tcs[2]))
    print(opt.get_paths(2).paths(tcs[2]))
    print(opt.get_paths(3).paths(tcs[2]))
    # print(opt._load_dict)
    # for k, v in opt._load_dict['bandwidth'].items():
    #     print(k, v)
    # print(pptc)
    # for tc in pptc.tcs():
    #     print(tc.volFlows)

    print(opt.volumes)

def test_churn():
    """ Check that we can correctly implement shortest path routing """
    # Generate a topology:
    topo = complete_topology(3)
    for l in topo.links():
        topo.set_resource(l, 'bandwidth', 3 * (3 - 1) * 100)

    # Generate a single traffic class:
    # TrafficClass (id, name, source node, destination node)
    tcs = [TrafficClass(0, u'classname', 0, 2, np.array([20, 30, 40, 50, 50, 50, 20]))]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, cutoff=100)
    # Application configuration
    # appconfig = {
    #     'name': u'minChurnApp',
    #     'constraints': [(Constraint.ROUTE_ALL, (pptc.tcs(),), {})],
    #     'obj': (Objective.MIN_CHURN, (), {}),
    #     'resource_cost': {}
    # }


    # # Create an application based on our config
    # app = App(pptc, **appconfig)
    # print(app.name)

    te_app = AppBuilder().name('te') \
        .pptc(pptc)\
        .add_constr(Constraint.ROUTE_ALL)\
        .objective(Objective.MIN_LINK_LOAD, resource="bandwidth")\
        .add_resource(name='bandwidth', applyto='links', cost_val=1).build()

    churn_app = AppBuilder().name('minchurn') \
        .pptc(pptc) \
        .objective(Objective.MIN_CHURN) \
        .build()

    caps = NetworkCaps(topo)
    caps.add_cap('bandwidth', cap=1)
    

    opt = compose_apps([te_app, churn_app], topo, NetworkConfig(caps))

    # Create and solve an optimization based on the app
    # No link capacities will just result in a single shortest path
    
    assert opt.is_solved()
    print(opt.get_solved_objective(te_app))
    print(opt.get_solved_objective(churn_app))
    
    print(opt.get_xps()[0, 0, :])
    print(opt.get_xps()[0, 1, :])

    print(opt.get_paths(0))
    print(opt.get_paths(1))
    print(opt.get_paths(2))
    # print(opt.get_paths(3))
    # print(opt.get_paths(4))
    
    # for pi, p in enumerate(paths.paths(tcs[0])):
    #     if list(p.nodes()) == [0, 2]:
    #         assert p.flow_fraction() == 1
    #     else:
    #         assert p.flow_fraction() == 0

    # # norm factor for latency is diameter * n^2
    # norm = topo.diameter() * 25
    # # the objective is 1-normalized latency, and latency is 1.
    # # because 1 path with flow fraction of 1.
    # solution = opt.get_solved_objective(app)[0]
    # assert solution == 1 - 1 / norm or abs(solution - 1 - 1 / norm) <= EPSILON
    # solution = opt.get_solved_objective()
    # assert solution == 1 - 1 / norm or abs(solution - 1 - 1 / norm) <= EPSILON

def main():
    # test_churn()
    # test_stable()
    test_min_alloc()

if __name__ == "__main__":
    CUR_DIR = os.path.dirname(os.path.abspath(__file__)) + "/"
    
    logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    main()