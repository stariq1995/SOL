# coding=utf-8
""" This script sets up and executes the optimization for ElasticTree [#elastictree]_


[#elastictree] Heller, B. et al. 2013. ElasticTree: Saving Energy in Data Center Networks. NSDI (2010).
"""

import networkx

from sol.optimization.formulation import getOptimization
from sol.optimization.formulation.funcs import defaultLinkFuncNoNormalize
from sol.optimization.path.generate import generatePathsPerTrafficClass
from sol.optimization.path.predicates import nullPredicate
from sol.optimization.path.select import chooserand
from sol.optimization.topology import generators
from sol.optimization.topology import provisioning
from sol.optimization.topology.provisioning import generateTrafficClasses

if __name__ == '__main__':

    # Let's create a topology first, as an example
    # ============================================
    topo = generators.generateCompleteTopology(10)
    # label our switches
    generators.forceSwitchLabels(topo)
    # For the sake of example, set middleboxes everywhere
    for node, data in topo.nodes():
        topo.setMbox(node)
        topo.setServiceTypes(node, ['switch', 'fw', 'ids'])

    # Resort to some default functions, obviously you'd provide your real data here
    # =============================================================================

    # ingress-egress pairs
    iePairs = provisioning.generateIEpairs(topo)
    # generate traffic matrix
    trafficMatrix = provisioning.computeUniformTrafficMatrixPerIE(
        iePairs, 10 ** 6)
    # compute traffic classes, only one class
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    # similartly with link capacities
    linkCaps = provisioning.provisionLinks(topo, trafficClasses, 3)
    # Fake power consumption. Imagine these are kw/h, whatever.
    switchPower = {node: 1500 for node, data in topo.nodes()}
    linkPower = {(u, v): 500 for u, v, data in topo.links()}

    # ======================
    # start our optimization
    # ======================
    opt = getOptimization()
    # generate the paths
    pptc = generatePathsPerTrafficClass(topo, trafficClasses, nullPredicate,
                                        networkx.diameter(topo.getGraph()) * 1.5,
                                        1000)
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

    # Now enforce disabled paths when we toggle links/nodes
    opt.addRequireSomeNodesConstraint(pptc, some=1)
    opt.addBudgetConstraint(topo, lambda n: 1, 5)

    # Now, set the objective, and value the switch power more.
    opt.setPredefinedObjective('minroutingcost', pptc=pptc)

    # Solve the formulation:
    # ======================
    opt.solve()

    # Print the objective function
    print opt.getSolvedObjective()

    ######
    # Total power consumption: 6875
    # If we kept everything on, it would be: 5 * 1500 + 500 * 10 = 12500
    ######