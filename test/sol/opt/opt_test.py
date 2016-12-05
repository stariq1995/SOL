# coding=utf-8
from numpy import array
from sol.opt.gurobiwrapper import get_obj_var
from sol.opt.quickstart import from_app
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.topology.traffic import TrafficClass

from sol.opt.app import App
from sol.topology.generators import complete_topology
from sol.utils.const import ALLOCATE_FLOW, ROUTE_ALL, OBJ_MIN_LATENCY, \
    RES_BANDWIDTH, OBJ_MAX_ALL_FLOW, CAP_LINKS


def test_shortest_path():
    # Generate a topology:
    topo = complete_topology(5)

    # Application configuration
    appconfig = {
        'name': u'minLatencyApp',
        'constraints': [ALLOCATE_FLOW, ROUTE_ALL],
        'obj': OBJ_MIN_LATENCY,
        'predicate': null_predicate,
        'resource_cost': {}
    }

    # Generate a single traffic class:
    # TrafficClass (id, name, source node, destination node)
    # For now don't worry about IP addresses.
    tcs = [TrafficClass(0, u'classname', 0, 2)]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, appconfig['predicate'],
                             cutoff=100)
    # Create an application based on our config
    app = App(pptc, **appconfig)

    # Create and solve an optimization based on the app
    # No link capacities will just result in a single shortest path
    opt = from_app(topo, app)
    opt.solve()

    paths = opt.get_paths()
    for pi, p in enumerate(pptc.paths(pptc.tc_byid(0))):
        if list(p.nodes()) == [0, 2]:
            assert p.flow_fraction() == 1
        else:
            assert p.flow_fraction() == 0


def test_maxflow():
    appconfig = {
        'name': u'mf',
        'constraints': [ALLOCATE_FLOW, (CAP_LINKS, RES_BANDWIDTH, 1)],
        'obj': OBJ_MAX_ALL_FLOW,
        'predicate': null_predicate,
        'resource_cost': {RES_BANDWIDTH: 2}
    }
    topo = complete_topology(4)
    for link in topo.links():
        topo.set_resource(link, RES_BANDWIDTH, 1)
    tcs = [TrafficClass(0, u'classname', 0, 2, array([3]))]
    pptc = generate_paths_tc(topo, tcs, null_predicate, cutoff=100)

    app = App(pptc, **appconfig)
    opt = from_app(topo, app)
    opt.solve()
    assert get_obj_var(app, opt) == .5

# TODO: bring back fixed paths
# def test_fixed_paths():
#     topo = mock_topo()
#     app = mock_max_flow_app(topo)
#     for tc in app.pptc:
#         for p in app.pptc[tc]:
#             p.set_flow_fraction(.008)
#
#     opt = from_app(topo, app)
#     opt.fix_paths(app.pptc)
#     opt.write(u'testfp')
#     opt.solve()
#     paths = opt.get_path_fractions(app.pptc)[0]
#     for tc in paths:
#         for p in app.pptc[tc]:
#             assert p.flow_fraction() == .008
