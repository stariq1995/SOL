# coding=utf-8
import pprint

from sol.topology.provisioning import generateTrafficClasses, provisionLinks

from sol.opt import initOptimization
from sol.path.predicates import nullPredicate
from sol.topology import Topology, TrafficMatrix


def TE():
    # ==============
    # Let's generate some example data;
    # ==============
    topo = Topology('Abilene', 'data/topologies/Abilene.graphml')
    # Let's load an existing gravity traffic matrix. It's just a dict mapping ingress-egress tuples to flow volume (a float).
    trafficMatrix = TrafficMatrix.load('data/tm/Abilene.tm')

    # compute traffic classes. We will only have one class that encompasses all the traffic;
    # assume that each flow consumes 2000 units of bandwidth
    trafficClasses = generateTrafficClasses(trafficMatrix.keys(), trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    # since our topology is "fake", provision our links and generate link capacities in our network
    linkcaps = provisionLinks(topo, trafficClasses, 2)
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
    opt.allocateFlow(pptc)

    # Traffic must not overload links -- so cap links according to our link constraints (recall the 50%)
    # linkcapfunc defines how bandwidth is consumed.
    linkcapfunc = lambda link, tc, path, resource: tc.volBytes / linkcaps[link]
    opt.capLinks(pptc, 'bandwidth', linkConstrCaps, linkcapfunc)

    # Route all the traffic
    opt.route_all(pptc)

    # Minimize the link load in the network (a pretty standard TE goal)
    opt.minLinkLoad('bandwidth')

    # Solve the optimization
    opt.solve()

    ### Results
    # Print the objective function --- this is the fractional load on the maximally loaded link
    print opt.getSolvedObjective()

    # pretty-print the paths on which the traffic is routed, along with the fraction for each traffic class
    for tc, paths in opt.getPathFractions(pptc).iteritems():
        print 'src:', tc.src, 'dst:', tc.dst, 'paths:', pprint.pformat(paths)


if __name__ == "__main__":
    TE()
