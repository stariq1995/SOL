# coding=utf-8
""" This script sets up and executes the optimization for ElasticTree [#elastictree]_


[#elastictree] Heller, B. et al. 2013. ElasticTree: Saving Energy in Data Center Networks. NSDI (2010).
"""

import networkx
from sol.opt.formulation import getOptimization
from sol.opt.formulation.funcs import defaultLinkFuncNoNormalize
from sol.opt.topology import generators
from sol.opt.topology import provisioning
from sol.opt.topology.provisioning import generateTrafficClasses

from sol.path import chooserand
from sol.path import generatePathsPerTrafficClass
from sol.path import nullPredicate

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
    opt.addDecisionVars(pptc)
    opt.addBinaryVars(pptc, topo, ['path', 'node', 'edge'])
    # then routing of traffic
    opt.allocateFlow(pptc)
    opt.routeAll(pptc)

    # then link capacities
    opt.capLinks(pptc, 'bandwidth', linkCaps, defaultLinkFuncNoNormalize)

    # Now enforce disabled paths when we toggle links/nodes
    opt.reqAllNodes(pptc)
    opt.reqAllEdges(pptc)
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