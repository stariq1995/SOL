# coding=utf-8

from sol.opt.quickstart import from_app
from sol.opt.app import App
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.topology.generators import complete_topology
from sol.topology.traffic import TrafficClass
from sol.utils.const import *

if __name__ == '__main__':

    # Generate a topology:
    topo = complete_topology(5)  # 5 nodes

    # Application configuration
    appconfig = {
        'name': u'minLatencyApp',
        'constraints': [ALLOCATE_FLOW, ROUTE_ALL],
        'obj': OBJ_MIN_LATENCY,
        'predicate': null_predicate,
        'resource_cost': {BANDWIDTH: 100}
    }

    # Generate a single traffic class:
    # TrafficClass (id, name, source node, destination node)
    # For now don't worry about IP addresses.
    tc = [TrafficClass(1, u'classname', 0, 4)]
    # Generate all paths for this traffic class
    pptc = generate_paths_tc(topo, tc, appconfig['predicate'],
                             cutoff=100)
    # Create an application based on our config
    app = App(pptc, **appconfig)

    # Create and solve an optimization based on the app
    opt = from_app(topo, app)
    opt.solve()

    # Get and print the resulting paths
    paths = opt.get_path_fractions(pptc)

    print (paths)
