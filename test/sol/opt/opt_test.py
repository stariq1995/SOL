# coding=utf-8

from sol.opt.app import App
from sol.opt.quickstart import from_app
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.topology.generators import complete_topology
from sol.topology.traffic import TrafficClass
from sol.utils.const import ALLOCATE_FLOW, ROUTE_ALL, OBJ_MIN_LATENCY, \
    RES_BANDWIDTH
from sol.utils.ph import listeq
from fixtures import mock_topo, mock_min_latency_app, mock_max_flow_app


def test_shortest_path():
    # Generate a topology:
    topo = complete_topology(8)  # 8 nodes

    # Application configuration
    appconfig = {
        'name': u'minLatencyApp',
        'constraints': [ALLOCATE_FLOW, ROUTE_ALL],
        'obj': OBJ_MIN_LATENCY,
        'predicate': null_predicate,
        'resource_cost': {RES_BANDWIDTH: 100}
    }

    # Generate a single traffic class:
    # TrafficClass (id, name, source node, destination node)
    # For now don't worry about IP addresses.
    tcs = [TrafficClass(1, u'classname', 0, 5)]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tcs, appconfig['predicate'],
                             cutoff=100)
    # Create an application based on our config
    app = App(pptc, **appconfig)

    # Create and solve an optimization based on the app
    # No link capacities will just result in a single shortest path
    opt = from_app(topo, app)
    opt.solve()

    # Get and print the resulting paths
    paths = opt.get_path_fractions(pptc)
    # we only had one epoch
    paths = paths[0]
    
    # one traffic class
    assert len(paths) == 1
    
    # one path
    tc = tcs[0]
    assert len(paths[tc]) == 1
    path = paths[tc][0]

    assert listeq(list(path.nodes()), [0, 5])
    assert path.flow_fraction() == 1.0


def test_fixed_paths():
    topo = mock_topo()
    app = mock_max_flow_app(topo)
    for tc in app.pptc:
        for p in app.pptc[tc]:
            p.set_flow_fraction(.008)

    opt = from_app(topo, app)
    opt.fix_paths(app.pptc)
    opt.write(u'testfp')
    opt.solve()
    paths = opt.get_path_fractions(app.pptc)[0]
    for tc in paths:
        for p in app.pptc[tc]:
            assert p.flow_fraction() == .008

