# coding=utf-8

import functools
import itertools
import pprint
from random import shuffle

import networkx

from sol.opt.funcs import defaultLinkFunc
from sol.path.predicates import useMboxModifier

from sol.opt import getOptimization, initOptimization
from sol.topology import provisioning
from sol.topology.provisioning import generateTrafficClasses

from sol.path import chooserand
from sol.path import generatePathsPerTrafficClass
from sol.topology import Topology, TrafficMatrix

if __name__ == '__main__':

    # Let's create our topology first, as an example
    # ============================================
    topo = Topology('Abilene', 'data/topologies/Abilene.graphml')
    # Let's load an existing gravity traffic matrix. It's just a dict mapping ingress-egress tuples to flow volume (a float).
    trafficMatrix = TrafficMatrix.load('data/tm/Abilene.tm')
    # set nodes to be firewalls and IDSes:
    for node in topo.nodes():
        topo.setMbox(node)
        topo.set_service_types(node, ['fw', 'ids'])

    trafficClasses = generateTrafficClasses(trafficMatrix.keys(), trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    # assign flow processing cost for each traffic class
    for t in trafficClasses:
        t.cpuCost = 10

    # Do some topology provisioning, instead of the real switch/link/middlebox capacities:
    # provision the node cpu capacities (for the sake of example)
    maxCPUCap = provisioning.compute_max_ingress_load(trafficClasses, {t: t.cpuCost for t in trafficClasses})
    nodeCaps = dict()
    nodeCaps['cpu'] = {node: maxCPUCap * 2 for node in topo.nodes()
                       if 'fw' or 'ids' in topo.get_service_types(node)}
    # provision the TCAM capacities on the switch nodes
    nodeCaps['tcam'] = {node: 1000 for node in topo.nodes()}
    # similartly with link capacities
    linkCaps = provisioning.provision_links(topo, trafficClasses, 3)


    # =====================================
    # Write our user defined capacity functions
    # =====================================

    def path_predicate(path, topology):
        # Firewall followed by IDS is the requirement for the path to be valid
        return any([s == ('fw', 'ids') for s in itertools.product(*[topology.get_service_types(node)
                                                                    for node in path.useMBoxes])])


    def nodeCapFunc(node, tc, path, resource, nodeCaps):
        # this computes the cost of processing the traffic class at a given node
        if resource == 'cpu' and node in nodeCaps['cpu']:
            return tc.volFlows * tc.cpuCost / nodeCaps[resource][node]
        else:
            raise ValueError("wrong resource")  # just in case

    def linkCapFunc(link, tc, path, resource, linkCaps):
        return tc.volBytes / linkCaps[link]

    # Curry the functions to conform to the required signature
    nodeFunc = functools.partial(nodeCapFunc, nodeCaps=nodeCaps)
    linkFunc = functools.partial(linkCapFunc, linkCaps=linkCaps)

    def TCAMCapFunc(node, tc, path, resource):
        # it would be best to test if node is a switch here, but we know all nodes are switches in this example
        if resource == 'tcam':
            return 2  # two rules per path on each switch, just as an example.
        else:
            raise ValueError("wrong resource")  # just in case


    # ======================
    # start our optimization
    # ======================
    # Get paths that conform to our path predicate, choose a subset of 5 randomly to route traffic on.
    opt, pptc = initOptimization(topo, trafficClasses, path_predicate,
                                 'random', 5, functools.partial(useMboxModifier, chainLength=2), 'CPLEX')

    # Allocate and route all of the traffic
    opt.allocate_flow(pptc)
    opt.route_all(pptc)

    # We know that we will need binary variables per path and node to model TCAM constraints
    opt._add_binary_vars(pptc, topo, ['path', 'node'])
    # Add TCAM capacities here
    opt.capNodesPathResource(pptc, 'tcam', nodeCaps['tcam'], TCAMCapFunc)

    # Now just add constraints for link capacities (use default Link Function, nothing fancy here)
    opt.capLinks(pptc, 'bandwidth', linkCaps, linkFunc)
    # And similarly node capacities
    # Recall that we are normalizing the CPU node load to [0, 1], so capacities are now all 1.
    opt.capNodes(pptc, 'cpu', {node: 1 for node in topo.nodes()
                               if 'fw' or 'ids' in topo.get_service_types(node)}, nodeFunc)

    # Finally, the objective, minimize the load on the middleboxes
    opt.minNodeLoad(pptc, 'cpu')

    # Solve the formulation:
    # ======================
    opt.solve()

    # Print the objective function --- in this case the load on the maximally loaded middlebox [0, 1]
    print opt.get_solved_objective()
    # pretty-print the paths on which the traffic is routed, along with the fraction for each traffic class
    # useMBoxes indicates at which middleboxes the processing should occur
    for tc, paths in opt.get_path_fractions(pptc).iteritems():
        print 'src:', tc.src, 'dst:', tc.dst, 'paths:', pprint.pformat(paths)
