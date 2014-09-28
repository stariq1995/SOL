""" Original Elastic formulation from the paper
"""
from __future__ import division
from collections import defaultdict
from panacea.lps.apps import apps

try:
    # noinspection PyUnresolvedReferences
    import cplex
except ImportError as e:
    print 'Need IBM CPLEX API, ' \
          'make sure it is installed and in your pythonpath'
    raise e
import itertools
import networkx as nx


def generateElasticOrigFormulation(topology, **kwargs):
    """ defines the original Elastic formulation
    :param topology: topology
    :param kwargs: any additional config options
    :return: the CPLEX problem instance (not solved)
    """
    G = topology.getGraph()
    commodities = kwargs.get('commodities')

    prob = cplex.Cplex()
    numEdges = G.number_of_edges()
    numNodes = G.number_of_nodes()
    numCommodities = len(commodities)
    prob.variables.add(names=['x_{}_{}'.format(u, v)
                              for u, v in G.edges_iter()],
                       lb=[0] * numEdges, ub=[1] * numEdges,
                       types=[prob.variables.type.binary] * numEdges
    )
    prob.variables.add(names=['y_{}'.format(u)
                              for u in G.nodes_iter()],
                       lb=[0] * numNodes, ub=[1] * numNodes,
                       types=[prob.variables.type.binary] * numNodes
    )
    prob.variables.add(names=['f_{}_{}_{}'.format(k.ID, u, v)
                              for k in commodities
                              for u, v in G.edges_iter()],
                       lb=[0] * numEdges * numCommodities,
                       ub=[1] * numEdges * numCommodities)
    prob.variables.add(names=['r_{}_{}_{}'.format(k.ID, u, v)
                              for k in commodities
                              for u, v in G.edges_iter()],
                       lb=[0] * numEdges * numCommodities,
                       ub=[1] * numEdges * numCommodities,
                       types=[prob.variables.type.binary] *
                            numEdges * numCommodities
    )

    prob.variables.add(names=['linkpower', 'switchpower'])

    v = prob.variables.get_names()
    varindex = dict(itertools.izip(v, range(len(v))))

    # capacity + binary on constraints:
    for u, v in G.edges_iter():
        if 'capacity' in G.edge[u][v]:
            var = defaultdict(lambda: 0)
            for k in commodities:
                var[varindex['f_{}_{}_{}'.format(k.ID, u, v)]] += \
                    k.volume * k.trafficClass.avgSize / G.edge[u][v]['capacity']
            var[varindex['x_{}_{}'.format(u, v)]] -= 1
            if var:
                var, mults = map(list, zip(*var.items()))
                prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                            rhs=[0], senses=['L'],
                                            names=[
                                                'linkcap.{}.{}'.format(u, v)])

    # Flow conservation
    for k in commodities:
        for w in G.nodes_iter():
            var = defaultdict(lambda: 0)
            for out in G.successors_iter(w):
                var[varindex['f_{}_{}_{}'.format(k.ID, w, out)]] += 1
            for inn in G.predecessors_iter(w):
                var[varindex['f_{}_{}_{}'.format(k.ID, inn, w)]] -= 1
            if var:
                if w == k.src:
                    rhs = 1
                elif w == k.dst:
                    rhs = -1
                else:
                    rhs = 0
                var, mults = map(list, zip(*var.items()))
                prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                            rhs=[rhs], senses=['E'])

    # Bidirectional link power
    for u, v in G.edges_iter():
        prob.linear_constraints.add(
            [cplex.SparsePair([varindex['x_{}_{}'.format(u, v)],
                               varindex['x_{}_{}'.format(v, u)]],
                              [1, -1])],
            rhs=[0], senses='E')

    # Correlate link and switch power:
    for u in G.nodes_iter():
        var = defaultdict(lambda: 0)
        for w in nx.all_neighbors(G, u):
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex['x_{}_{}'.format(u, w)],
                                   varindex['y_{}'.format(u)]],
                                  [1, -1]),
                 cplex.SparsePair([varindex['x_{}_{}'.format(w, u)],
                                   varindex['y_{}'.format(u)]],
                                  [1, -1])],
                rhs=[0, 0], senses='LL')
            var[varindex['x_{}_{}'.format(w, u)]] = 1
        if var:
            var, mults = map(list, zip(*var.items()))
            prob.linear_constraints.add([cplex.SparsePair(
                var + [varindex['y_{}'.format(u)]], mults + [-1])],
                                        rhs=[0], senses=['G'])

    # Flow splitting constraints:
    for k in commodities:
        for u, v in G.edges_iter():
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex['f_{}_{}_{}'.format(k.ID, u, v)],
                                   varindex['r_{}_{}_{}'.format(k.ID, u, v)]],
                                  [1, -1])],
                rhs=[0], senses=['E'])

    # define link and switch power
    lp = apps['Elastic'].get('linkPower')
    sp = apps['Elastic'].get('switchPower')
    norm = lp * numEdges + sp * numNodes
    print norm
    prob.linear_constraints.add([cplex.SparsePair(
        [varindex['x_{}_{}'.format(u, v)] for u, v in G.edges_iter()] +
        [varindex['linkpower']],
        [lp / norm] * numEdges + [-1])],
                                rhs=[0], senses=['E'])
    prob.linear_constraints.add([cplex.SparsePair(
        [varindex['y_{}'.format(u)] for u in G.nodes_iter()] +
        [varindex['switchpower']],
        [sp / norm] * numNodes + [-1])],
                                rhs=[0], senses=['E'])

    # Objective:
    prob.objective.set_sense(prob.objective.sense.minimize)
    prob.objective.set_linear([(varindex['linkpower'], 1.0),
                               (varindex['switchpower'], 1.0)])
    gap = kwargs.get('mipgap', 0.005)
    prob.parameters.mip.tolerances.mipgap.set(gap)

    return prob
