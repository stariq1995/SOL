""" This script sets up and executes the optimization for SIMPLE [#simple]_


[#simple] Qazi, Z. et al. 2013. SIMPLE-fying Middlebox Policy Enforcement Using
SDN. SIGCOMM (2013).
"""

import functools
import itertools
import networkx

from sol.optimization.formulation import getOptimization
from sol.optimization.formulation.funcs import defaultLinkFunc, defaultNodeCapFunc
from sol.optimization.path.generate import generatePathsPerTrafficClass
from sol.optimization.path.predicates import useMboxModifier
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

    # =====================================
    # Write out user defined functions now:
    # =====================================

    def SIMPLE_predicate(path, topology):
        # our firewall followed by IDS is the requirement for the path
        return any([s == ('fw', 'ids') for s in itertools.product(*[topology.getServiceTypes(node)
                                                                  for node in path.useMBoxes])])

    def SIMPLE_NodeCapFunc(node, tc, path, resource, nodeCaps):
        # this computes the cost of processing the traffic
        if resource == 'cpu':
            return tc.volFlows * tc.cpuCost / nodeCaps[resource][node]
        elif resource == 'tcam':
            return 1  # this is per path cost

    # ======================
    # start our optimization
    # ======================
    opt = getOptimization()
    # generate the paths
    pptc = generatePathsPerTrafficClass(topo, trafficClasses, SIMPLE_predicate,
                                        networkx.diameter(topo.getGraph())*1.5,
                                        1000, functools.partial(useMboxModifier, chainLength=2))
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
    opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkCaps, functools.partial(defaultLinkFunc, linkCaps=linkCaps))
    # then node capacities
    capFunc = functools.partial(SIMPLE_NodeCapFunc, nodeCaps=nodeCaps)
    opt.addNodeCapacityConstraint(pptc, 'cpu', nodeCaps['cpu'], capFunc)
    opt.addNodeCapacityPerPathConstraint(pptc, 'tcam', nodeCaps['tcam'], capFunc)

    # finally, the objective
    opt.setPredefinedObjective('minmaxnodeload', 'cpu')

    # Solve the formulation:
    # ======================
    opt.write('/tmp/simple.lp')
    opt.solve()

    # Print the objective function
    print opt.getSolvedObjective()

    # Get the solution
    pathFractions = opt.getPathFractions(pptc)