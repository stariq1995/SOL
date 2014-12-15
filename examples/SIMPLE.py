""" This script sets up and executes the optimization for SIMPLE [#simple]_


[#simple] Qazi, Z. et al. 2013. SIMPLE-fying Middlebox Policy Enforcement Using
SDN. SIGCOMM (2013).
"""

import functools
import itertools

from sol.optimization.formulation import generateFormulation
from sol.optimization.formulation.funcs import defaultLinkFunc, defaultNodeCapFunc
from sol.optimization.path.predicates import useMboxModifier
from sol.optimization.topology import generators
from sol.optimization.topology import provisioning
from sol.optimization.topology.provisioning import generateTrafficClasses


if __name__ == '__main__':

    # TODO: add topologyzoo loader
    # Let's create a topology first, as an example
    topo = generators.generateCompleteTopology(5)
    # label our switches
    generators.forceSwitchLabels(topo)
    # For the sake of example, set middleboxes everywhere
    for node, data in topo.nodes():
        topo.setMbox(node)
        topo.setServiceTypes(node, ['switch', 'fw', 'ids'])
    iePairs = provisioning.generateIEpairs(topo)
    trafficMatrix = provisioning.computeUniformTrafficMatrixPerIE(
        iePairs, 10 ** 6)
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    for t in trafficClasses:
        t.cpuCost = 10
    maxCPUCap = provisioning.computeMaxIngressLoad(trafficClasses, {t: t.cpuCost for t in trafficClasses})
    nodeCaps = {}
    nodeCaps['cpu'] = {node: maxCPUCap * 2 for node, data in topo.nodes()
                    if 'fw' or 'ids' in topo.getServiceTypes(node)}

    linkCaps = provisioning.provisionLinks(topo, trafficClasses, 3)



    def SIMPLE_predicate(path, topology):
        # print path.useMBoxes
        # print [topology.getServiceTypes(node) for node in path.useMBoxes]
        # print [s for s in itertools.product(*[topology.getServiceTypes(node) for node in path.useMBoxes])]

        # return True
        return any([s == ('fw', 'ids') for s in itertools.product(*[topology.getServiceTypes(node)
                                                                  for node in path.useMBoxes])])

    def SIMPLE_NodeCapFunc(node, tc, path, resource, nodeCaps):
        if resource == 'cpu':
            return tc.volFlows * getattr(tc, '{}Cost'.format(resource)) / nodeCaps[node][resource]
        elif resource == 'tcam':
            return 1


    # Setup the basic config
    config = {
        'name': 'SIMPLE',  # for clarity

        'topology': topo,
        'trafficClasses': trafficClasses,

        'predicate': SIMPLE_predicate,
        'pathModifier': functools.partial(useMboxModifier, chainLength=2),
        'selectStrategy': 'random',
        'selectNumber': 10,

        'nodeCaps': nodeCaps,
        'linkCaps': linkCaps,
        'nodeCapFunction': functools.partial(SIMPLE_NodeCapFunc, nodeCaps=nodeCaps),
        'linkCapFunction': functools.partial(defaultLinkFunc, linkCaps=linkCaps),
        'constraints': [('nodecap', 'cpu'), 'allocateflow', 'routeall', ('linkcap', 'bandwidth'),
            ('nodecapIfActive', 'tcam')],
        'objective': ('minMaxNodeLoad', 'cpu')
    }

    # Generate the formulation
    problem, pptc = generateFormulation(**config)
    problem.write('/tmp/simple.lp')
    # raise Exception

    # Solve the formulation:
    problem.solve()
    print problem.getSolvedObjective()

    # Get the solution
    pathFractions = problem.getPathFractions(pptc)

    # Put it on the network using OpenDaylight (mediocre implementation)
    # FIXME: This is experimental