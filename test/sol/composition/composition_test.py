import networkx as nx
from sol.opt.composer import composeSingleLP
from sol.topology.provisioning import generateTrafficClasses

from sol import App, RES_COMPOSE_CONFLICT, MIN_LINK_LOAD, MIN_LATENCY
from sol.path import generatePathsPerTrafficClass, kShortestPaths
from sol.path.predicates import nullPredicate
from sol.topology import provisioning
from sol.topology.generators import generateCompleteTopology


def flatten(d):
    return reduce(lambda x, y: x + y, list(d.values()), [])


def test_composition_1():
    topo = generateCompleteTopology(3)

    iePairs = provisioning.generateIEpairs(topo)
    trafficMatrix = provisioning.uniformTM(iePairs, 10 ** 6)
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix,
                                            {'app1': .6, 'app2': .4},
                                            classBytesDict={'app1': 10, 'app2': 10},
                                            asdict=True)
    linkCaps = provisioning.provisionLinks(topo, flatten(trafficClasses), 1)

    pptc1 = generatePathsPerTrafficClass(topo, trafficClasses['app1'], nullPredicate,
                                         nx.diameter(topo.getGraph()) * 1.5)
    pptc1 = kShortestPaths(pptc1, 10)
    pptc2 = generatePathsPerTrafficClass(topo, trafficClasses['app2'], nullPredicate,
                                         nx.diameter(topo.getGraph()) * 1.5)
    pptc2 = kShortestPaths(pptc2, 10)

    apps = [
        App(pptc1, {'bw': 10}, MIN_LINK_LOAD, 'app1'),
        App(pptc2, {'bw': 10}, MIN_LATENCY, 'app2')
    ]

    nodeCaps = {n: {} for n in topo.nodes(False)}
    linkCaps = {l: {'bw': linkCaps[l]} for l in linkCaps}

    opt = composeSingleLP(apps, topo, RES_COMPOSE_CONFLICT, nodeCaps, linkCaps)
    opt.write('testc1')
    opt.solve()
    assert opt.isSolved()

    # opt.getGurobiModel().computeIIS()
    # opt.getGurobiModel().write("model.ilp")
