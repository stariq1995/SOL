# coding=utf-8
""" This script sets up and executes the optimization for SIMPLE [#simple]_


[#simple] Qazi, Z. et al. 2013. SIMPLE-fying Middlebox Policy Enforcement Using
SDN. SIGCOMM (2013).
"""

import functools
import itertools

import networkx
from sol.opt.formulation import getOptimization
from sol.opt.formulation.funcs import defaultLinkFuncNoNormalize
from sol.opt.topology import generators
from sol.opt.topology import provisioning
from sol.opt.topology.provisioning import generateTrafficClasses

from sol.path import chooserand
from sol.path import generatePathsPerTrafficClass
from sol.path import useMboxModifier

if __name__ == '__main__':

    # Let's create a topology first, as an example
    # ============================================
    topo = generators.extractTopo()
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
    # Write our user defined functions now:
    # =====================================

    def SIMPLE_predicate(path, topology):
        # Firewall followed by IDS is the requirement for the path
        return any([s == ('fw', 'ids') for s in itertools.product(*[topology.getServiceTypes(node)
                                                                    for node in path.useMBoxes])])

    def SIMPLE_NodeCapFunc(node, tc, path, resource, nodeCaps):
        # this computes the cost of processing the traffic class at
        if resource == 'cpu' and node in nodeCaps['cpu']:
            return tc.volFlows * tc.cpuCost / nodeCaps[resource][node]
        else:
            raise ValueError("wrong resource")  # just in case
    # Curry the function
    capFunc = functools.partial(SIMPLE_NodeCapFunc, nodeCaps=nodeCaps)

    def SIMPLE_TCAMFunc(node, tc, path, resource):
        # it would be best to test if node is a switch here, but we know all nodes are switches in this scenario
        if resource == 'tcam':
            return 2  # two rules per path on each switch, as an example.
        else:
            raise ValueError("wrong resource")  # just in case

    # ======================
    # start our optimization
    # ======================
    opt = getOptimization()
    # generate the paths
    pptc = generatePathsPerTrafficClass(topo, trafficClasses, SIMPLE_predicate,
                                        networkx.diameter(topo.getGraph()) * 1.5,
                                        1000, functools.partial(useMboxModifier, chainLength=2))
    # randomly choose 5 paths per traffic class
    pptc = chooserand(pptc, 5)

    # add all the constraints
    # variables go first
    opt.addDecisionVariables(pptc)
    # we know that we will need binary variables per path and node. (because we read the paper)
    opt.addBinaryVariables(pptc, topo, ['path', 'node'])
    # then routing of traffic
    opt.addAllocateFlowConstraint(pptc)
    opt.addRouteAllConstraint(pptc)

    # then link capacities (use default Link Function, nothing fancy here)
    opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkCaps, defaultLinkFuncNoNormalize)

    # then node capacities
    # recall we are normalizing the CPU node load, so capacities are now all 1.
    opt.addNodeCapacityConstraint(pptc, 'cpu', {node: 1 for node, data in topo.nodes()
                                                if 'fw' or 'ids' in topo.getServiceTypes(node)}, capFunc)
    opt.addNodeCapacityPerPathConstraint(pptc, 'tcam', nodeCaps['tcam'], SIMPLE_TCAMFunc)

    # finally, the objective
    opt.setPredefinedObjective('minmaxnodeload', resource='cpu')

    # Solve the formulation:
    # ======================
    opt.solve()

    # Print the objective function
    print opt.getSolvedObjective()
    print opt.getPathFractions(pptc)
