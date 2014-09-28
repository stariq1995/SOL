"""
Original Merlin implementation from the paper
"""
from __future__ import division

try:
    # noinspection PyUnresolvedReferences
    import cplex
except ImportError as ex:
    print 'Need IBM CPLEX API, ' \
          'make sure it is installed and in your pythonpath'
    raise ex
import itertools
import networkx as nx
from ....util.exceptions import UnsupportedOperationException
from collections import defaultdict
from panacea.util.pythonHelper import Tree


def generateMerlinOrigFormulation(topology, commodities, classes,
                                  mipgap=0.005):
    # All resources that we are keeping track of
    """

    :param topology:
    :param commodities:
    :param classes:
    :param mipgap:
    :raise UnsupportedOperationException:
    """

    classes = classes
    if len(classes) > 1:
        raise UnsupportedOperationException('So far multi-class LPs '
                                            'are not supported')
    cl = classes[0]
    topograph = topology.getGraph()

    # Construct our G_i's, each using an NFA
    gis = []
    for k in commodities:
        gi = nx.DiGraph()
        source = 'source{}'.format(k.ID)
        sink = 'sink{}'.format(k.ID)
        badmiddle = {k.src, k.dst}
        # now construct nfa
        # The NFA graph (make this simple, only one regex that requires one
        # middlebox):
        nfa = nx.DiGraph()
        nfa.add_nodes_from(range(5))
        nfa.add_edge(0, 1, label=[k.src])
        nfa.add_edge(1, 1, label=set(topograph.nodes()).difference(badmiddle))
        nfa.add_edge(1, 2, label=[n for n in topograph.nodes_iter()
                                  if 'hasmbox' in topograph.node[n]])
        nfa.add_edge(2, 2, label=set(topograph.nodes()).difference(badmiddle))
        nfa.add_edge(2, 3, label=[k.dst])
        nfa.add_edge(3, 4, label=[sink])

        gi.add_nodes_from(itertools.product(topograph.nodes(), nfa.nodes()))
        transitions = nfa.edges()
        topoedges = topograph.edges()
        for u, q in gi.nodes_iter():
            for v, qp in gi.nodes_iter():
                if (u == v or (u, v) in topoedges) \
                        and ((q, qp) in transitions
                             and v in nfa.edge[q][qp]['label']):
                    gi.add_edge((u, q), (v, qp))
        # add source and sink
        gi.add_node(source)
        gi.add_node(sink)
        gi.add_edge(source, (k.src, 1))
        gi.add_edge((k.dst, 3), sink)
        gis.append(gi)

    prob = cplex.Cplex()

    # Add edge flow fractions:
    edges = Tree()
    for i, Gi in enumerate(gis):
        edgeslocal = dict([(edge, index) for (index, edge)
                           in enumerate(Gi.edges_iter())])
        prob.variables.add(names=['xe_{}_{}'.format(i, index)
                                  for index in edgeslocal.itervalues()],
                           types=[prob.variables.type.binary] *
                                 len(edgeslocal),
                           lb=[0] * len(edgeslocal),
                           ub=[1] * len(edgeslocal))
        edges[i] = edgeslocal
    prob.variables.add(names=['maxlinkload'], lb=[0], ub=[1])

    # Flow conservation:
    v = prob.variables.get_names()
    varindex = dict(itertools.izip(v, range(len(v))))
    for i, Gi in enumerate(gis):
        for node in Gi.nodes_iter():
            var = defaultdict(lambda: 0)
            for out in Gi.out_edges_iter([node]):
                var[varindex['xe_{}_{}'.format(i, edges[i][out])]] += 1
            for inn in Gi.in_edges_iter([node]):
                var[varindex['xe_{}_{}'.format(i, edges[i][inn])]] -= 1
            if var:
                if isinstance(node, str) and node.startswith('source'):
                    rhs = 1
                elif isinstance(node, str) and node.startswith('sink'):
                    rhs = -1
                else:
                    rhs = 0
                var, mults = map(list, zip(*var.items()))
                prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                            rhs=[rhs], senses=['E'])

    # Edge capacity:
    # print commodities
    for u, v in topograph.edges_iter():
        if 'capacity' in topograph.edge[u][v]:
            var = defaultdict(lambda: 0)
            for i, Gi in enumerate(gis):
                k = commodities[i]
                subedges = [e for e in Gi.edges_iter()
                            if (e[0][0] == u and e[1][0] == v) or
                            (e[0][0] == v and e[1][0] == u)]
                for e in subedges:
                    var[varindex['xe_{}_{}'.format(i, edges[i][e])]] += \
                        k.volume * cl.avgSize \
                        / topograph.edge[u][v]['capacity']
            if var:
                var2, mults = map(list, zip(*var.items()))
                prob.linear_constraints.add([cplex.SparsePair(var2, mults)],
                                            rhs=[1],
                                            senses='L')
            var[varindex['maxlinkload']] = -1
            var2, mults = map(list, zip(*var.items()))
            prob.linear_constraints.add([cplex.SparsePair(var2, mults)],
                                        rhs=[0],
                                        senses='L')

    # Objective:
    prob.objective.set_sense(prob.objective.sense.minimize)
    prob.objective.set_linear('maxlinkload', 1.0)
    gap = mipgap
    prob.parameters.mip.tolerances.mipgap.set(gap)

    return prob
