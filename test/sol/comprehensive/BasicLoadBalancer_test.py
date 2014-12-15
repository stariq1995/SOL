
import functools

from sol.optimization.formulation import generateFormulation
from sol.optimization.formulation.funcs import defaultLinkFunc, defaultNodeCapFunc
from sol.optimization.path.predicates import nullPredicate, useMboxModifier
from sol.optimization.topology import generators
from sol.optimization.topology import provisioning
from sol.optimization.topology.provisioning import generateTrafficClasses


def testBasicLoadBalancer():
    # Let's create a topology first, as an example
    topo = generators.generateChainTopology(4)
    # label our switches
    generators.forceSwitchLabels(topo)
    # For the sake of example, set middleboxes everywhere
    for node, data in topo.nodes():
        topo.setMbox(node)
        topo.setServiceTypes(node, ['dpi'])
    iePairs = [(0, 3)]
    trafficMatrix = provisioning.computeUniformTrafficMatrixPerIE(
        iePairs, 100)
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 10})
    for t in trafficClasses:
        t.cpuCost = 10
    maxCPUCap = provisioning.computeMaxIngressLoad(trafficClasses, {t: t.cpuCost for t in trafficClasses})
    assert maxCPUCap == 1000
    nodeCaps = {node: maxCPUCap for node, data in topo.nodes()
                if 'dpi' in topo.getServiceTypes(node)}
    linkCaps = provisioning.provisionLinks(topo, trafficClasses, 2)
    assert linkCaps.values().pop() == 2000

    # Setup the basic config
    config = {
        'name': 'BasicLoadBalancer',  # for clarity

        'topology': topo,

        'trafficClasses': trafficClasses,
        'predicate': nullPredicate,
        'pathModifier': useMboxModifier,
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
    assert problem is not None
    assert pptc is not None

    # Solve the formulation:
    problem.solve()
    assert problem.getSolvedObjective() == .25