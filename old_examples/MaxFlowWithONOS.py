# coding=utf-8

from sol.topology.provisioning import generateTrafficClasses

from sol.opt import initOptimization
from sol.path.predicates import nullPredicate
from sol.sdn.controllerUtil import computeSplit
from sol.sdn.onosWrapper import ONOSInterface
from sol.topology import provisioning
from sol.topology.generators import complete_topology


def MaxFlow():
    # ==============
    # Let's generate some example data; SOL has some functions to help with that.
    # ==============
    # A complete topology
    topo = complete_topology(5)
    # ingress-egress pairs, between which the traffic will flow
    iePairs = [(0, 3)]
    # generate a traffic matrix, in this case, a uniform traffic matrix with a million flows
    trafficMatrix = provisioning.uniformTM(
        iePairs, 10 ** 6)
    # compute traffic classes. We will only have one class that encompasses all the traffic;
    # assume that each flow consumes 2000 units of bandwidth
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    # since our topology is "fake", provision our links and generate link capacities in our network
    linkcaps = provisioning.provision_links(topo, trafficClasses, 1)
    # these will be our link constraints: do not load links more than 50%
    linkConstrCaps = {(u, v): .5 for u, v in topo.links()}

    # ==============
    # Optimization
    # ==============

    # Start our optimization.
    # SOL automatically takes care of the path generation, but it needs the topology, traffic classes, path predicate
    # and path selection strategy.
    # nullPredicate means any path will do, no specific service chaining or policy requirements.
    # Then, SOL will choose maximum of 5 shortest paths for each traffic class to route traffic on.
    opt, pptc = initOptimization(topo, trafficClasses, nullPredicate, 'shortest', 5, backend='CPLEX')

    # Now, our constraints.
    # First, we must allocate some amount of flow (i.e, tell SOL to route things frorm ingress to egress)
    opt.allocate_flow(pptc)

    # Traffic must not overload links -- so cap links according to our link constraints (recall the 50%)
    # linkcapfunc defines how bandwidth is consumed.
    linkcapfunc = lambda link, tc, path, resource: tc.volBytes / linkcaps[link]
    opt.capLinks(pptc, 'bandwidth', linkConstrCaps, linkcapfunc)

    # Push as much traffic as we can
    opt.maxFlow(pptc)

    # Solve the optimization
    opt.solve()

    # For simple applications we can interface with ONOS and setup forwarding routes automatically:
    # Insert correct address to the web interface here;
    # You must ensure that ONOS is running the SOL app to be able to install rules in a batch
    onos = ONOSInterface("localhost:8181")
    routes = {}
    for tc, paths in opt.get_path_fractions(pptc).iteritems():
        routes.update(computeSplit(tc, paths, 0))
    onos.push_routes(routes)
    print("Done")


if __name__ == "__main__":
    MaxFlow()
