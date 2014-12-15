
import functools

from sol.optimization.formulation import generateFormulation
from sol.optimization.formulation.funcs import defaultLinkFunc, defaultNodeCapFunc
from sol.optimization.path.predicates import nullPredicate
from sol.optimization.topology import generators
from sol.optimization.topology import provisioning
from sol.optimization.topology.provisioning import generateTrafficClasses


def runBasicLoadBalancer():
    # Let's create a topology first, as an example
    topo = generators.generateChainTopology(4)
    # label our switches
    generators.forceSwitchLabels(topo)
    # For the sake of example, set middleboxes everywhere
    for node, data in topo.nodes():
        topo.setMbox(node)
        topo.setServiceTypes(node, ['dpi'])
    iePairs = provisioning.generateIEpairs(topo)
    trafficMatrix = provisioning.computeUniformTrafficMatrixPerIE(
        iePairs, 10 ** 6)
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 100})
    for t in trafficClasses:
        t.cpuCost = 10
    maxCPUCap = provisioning.computeMaxIngressLoad(trafficClasses, {t: t.cpuCost for t in trafficClasses})
    nodeCaps = {node: maxCPUCap for node, data in topo.nodes()
                if 'dpi' in topo.getServiceTypes(node)}
    linkCaps = provisioning.provisionLinks(topo, trafficClasses, 2)

    # Setup the basic config
    config = {
        'name': 'BasicLoadBalancer',  # for clarity

        'topology': topo,

        'trafficClasses': trafficClasses,
        'predicate': nullPredicate,
        'selectStrategy': 'random',
        'selectNumber': 10,
        'nodeCaps': nodeCaps,
        'linkCaps': linkCaps,
        'nodeCapFunction': functools.partial(defaultNodeCapFunc, nodeCaps=nodeCaps),
        'linkCapFunction': functools.partial(defaultLinkFunc, linkCaps=linkCaps),
        'constraints': [('nodecap', 'cpu'), 'allocateflow', 'routeall', ('linkcap', 'bandwidth')],
        'objective': ('minMaxNodeLoad', 'cpu')
    }

    # Generate the formulation
    problem, pptc = generateFormulation(**config)
    problem.write('/tmp/simple.lp')
    # raise Exception

    # Solve the formulation:
    problem.solve()
    print problem.getSolvedObjective()

if __name__ == '__main__':
    runBasicLoadBalancer()