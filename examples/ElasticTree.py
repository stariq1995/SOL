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
    topo = generators.generateCompleteTopology(5)
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
    # assign flow processing cost for each traffic class
    for t in trafficClasses:
        t.cpuCost = 10
    # provision the node cpu capacities
    maxCPUCap = provisioning.computeMaxIngressLoad(trafficClasses, {t: t.cpuCost for t in trafficClasses})
    nodeCaps = dict()
    nodeCaps['cpu'] = {node: maxCPUCap * 2 for node, data in topo.nodes()
                       if 'fw' or 'ids' in topo.getServiceTypes(node)}
    # and the tcam capacities
    nodeCaps['tcam'] = {node: 1000 for node, data in topo.nodes()}
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
    opt.addBinaryVariables(pptc, topo, ['path', 'node', 'edge'])
    # then routing of traffic
    opt.addAllocateFlowConstraint(pptc)
    opt.addRouteAllConstraint(pptc)

    # then link capacities
    opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkCaps, defaultLinkFuncNoNormalize)

    # Now enforce disabled paths when we toggle links/nodes
    opt.addRequireAllNodesConstraint(pptc)
    opt.addRequireAllEdgesConstraint(pptc)
    opt.addPathDisableConstraint(pptc)

    # finally, the objective
    # This one is trickier, we need fine-grained control over the objective
    # First, define additional variables:
    # Set switch power to the sum of switch consumptions of enabled nodes
    # So the constraint would look as follows:
    # SwitchPower = 1500 b_1 + 1500 b_2 + ... + 1500 b_n
    opt.defineVar('SwitchPower', {opt.bn(node): switchPower[node] for node, data in topo.nodes()})
    # Very similarly, compute total link power
    opt.defineVar('LinkPower', {opt.be(u, v): linkPower[(u, v)] for u, v, data in topo.links()})

    # Now, set the objective, and value the switch power more.
    opt.setObjectiveCoeff({'SwitchPower': .75, 'LinkPower': .25}, 'min')

    # Solve the formulation:
    # ======================
    opt.solve()

    # Print the objective function
    print opt.getSolvedObjective()

    ######
    # Total power consumption: 6875
    # If we kept everything on, it would be: 5 * 1500 + 500 * 10 = 12500
    ######