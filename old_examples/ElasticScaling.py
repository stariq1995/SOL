import itertools
from random import randint

import networkx
from sol.opt.topology.topology import Topology

from sol.opt import getOptimization
from sol.opt.funcs import defaultLinkFuncNoNormalize
from sol.path import generatePathsPerTrafficClass
from sol.path import hasMboxPredicate, useMboxModifier
from sol.path import chooserand
from sol.topology import generators
from sol.topology import provisioning
from sol.topology import generateTrafficClasses

if __name__ == '__main__':

    # Let's create a topology first, as an example
    # ============================================
    topo = Topology('star', networkx.star_graph(11).to_directed())
    # label our switches
    generators.forceSwitchLabels(topo)
    # For the sake of example, set middleboxes everywhere
    for node, data in topo.nodes():
        topo.setMbox(node)
        topo.setServiceTypes(node, ['switch', 'dpis'])

    # Resort to some default functions, obviously you'd provide your real data here
    # =============================================================================

    # ingress-egress pairs
    G = topo.getGraph()
    iePairs = [(i, e) for i, e in itertools.product(topo.nodes(False), repeat=2)
               if i != e and G.out_degree(i) == 1 and G.out_degree(e) == 1]
    print iePairs
    # generate traffic matrix
    populations = {node: randint(1 << 15, 1 << 18) for node, data in topo.nodes()}
    trafficMatrix = provisioning.computeGravityTrafficMatrixPerIE(
        iePairs, 10 ** 6, populations)
    # compute traffic classes, only one class
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    # assign flow processing cost for each traffic class
    for t in trafficClasses:
        t.cpuCost = 10
    # provision the node cpu capacities
    nodeCaps = {node: None for node, data in topo.nodes()}
    # similartly with link capacities
    linkCaps = provisioning.provisionLinks(topo, trafficClasses, 3)

    # ======================
    # start our optimization
    # ======================
    opt = getOptimization()
    # generate the paths
    pptc = generatePathsPerTrafficClass(topo, trafficClasses, hasMboxPredicate,
                                        networkx.diameter(topo.getGraph()) * 1.5,
                                        1000, useMboxModifier)
    # randomly choose 5 paths per traffic class
    pptc = chooserand(pptc, 5)

    # add all the constraints
    # variables go first
    opt.addDecisionVariables(pptc)
    opt.addBinaryVariables(pptc, topo, ['path', 'node'])
    # then routing of traffic
    opt.addAllocateFlowConstraint(pptc)
    opt.addRouteAllConstraint(pptc)

    # then link capacities
    opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkCaps, defaultLinkFuncNoNormalize)
    # then node capacities
    opt.addNodeCapacityConstraint(pptc, 'cpu', nodeCaps,
                                  lambda node, tc, path, resource: tc.volFlows * tc.cpuCost)
    opt.addRequireSomeNodesConstraint(pptc, some=1)
    opt.addPathDisableConstraint(pptc)
    opt.addBudgetConstraint(topo, lambda node: 1, 5)
    # opt.addCapacityBudgetConstraint('cpu', nodeCaps.keys(), 10 ** 9) # optional

    opt.setPredefinedObjective('minmaxnodeload', resource='cpu')

    # opt.write('/tmp/escale.lp')
    # Solve the formulation:
    # ======================
    opt.solve()

    # Print the objective function
    print opt.getSolvedObjective()
    # Print allocated capacities
    vals = opt.getAllVariableValues()
    for node in nodeCaps:
        print node, vals[opt.nc(node, 'cpu')], vals[opt.nl(node, 'cpu')]