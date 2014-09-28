""" Original panopticon formulation from the paper
"""
import cplex

from panacea.lps.apps import apps


__author__ = 'victor'


def generateFormulationPanopticonOrig(topology, commodities, lp=False):
    """

    :param topology:
    :param commodities:
    :return:
    """
    prob = cplex.Cplex()
    G = topology.getGraph()

    tmp = len(commodities) * G.number_of_edges()
    prob.variables.add(names=['x_{}_{}_{}'.format(k.ID, i, j) for k in
                              commodities for (i, j) in G.edges_iter()],
                       types=[prob.variables.type.continuous if lp else
                              prob.variables.type.binary] *
                             tmp,
                       lb=[0] * tmp, ub=[1] * tmp)
    tmp = len(commodities) * G.number_of_nodes()
    prob.variables.add(names=['u_{}_{}'.format(k.ID, i) for k in commodities
                              for i in G.nodes_iter()],
                       types=[prob.variables.type.continuous if lp else
                              prob.variables.type.binary] * tmp,
                       lb=[0] * tmp, ub=[1] * tmp)
    prob.variables.add(names=['y_{}'.format(i) for i in G.nodes_iter()],
                       types=[prob.variables.type.continuous if lp else
                              prob.variables.type.binary] *
                             G.number_of_nodes(),
                       lb=[0] * G.number_of_nodes(),
                       ub=[1] * G.number_of_nodes())
    varind = {v: i for i, v in enumerate(prob.variables.get_names())}

    # eq 2
    vs = []
    ms = []
    for node in G.nodes_iter():
        vs.append(varind['y_{}'.format(node)])
        ms.append(1)
    rhs = topology.getNumNodes('switch')
    prob.linear_constraints.add([cplex.SparsePair(vs, ms)],
                                rhs=[rhs], senses='L')

    for k in commodities:
        # eq 4
        for node in G.nodes_iter():
            vs = []
            ms = []
            for out in G.successors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, node, out)])
                ms.append(1)

            for inn in G.predecessors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, inn, node)])
                ms.append(-1)
            if node == k.src:
                rhs = 1
            elif node == k.dst:
                rhs = -1
            else:
                rhs = 0
            prob.linear_constraints.add([cplex.SparsePair(vs, ms)],
                                        rhs=[rhs], senses='E')
        vs = []
        ms = []
        # eq 5 & 6
        for node in G.nodes_iter():
            vs.append(varind['u_{}_{}'.format(k.ID, node)])
            ms.append(1)
            # eq 6
            prob.linear_constraints.add(
                [cplex.SparsePair([varind['u_{}_{}'.format(k.ID, node)],
                                   varind['y_{}'.format(node)]],
                                  [1, -1])],
                rhs=[0], senses='L')
        # eq 5
        prob.linear_constraints.add([cplex.SparsePair(vs, ms)], rhs=[1],
                                    senses='G')


        # eq 7
        for node in G.nodes_iter():
            vs = []
            ms = []
            for out in G.successors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, node, out)])
                ms.append(1)
            for inn in G.predecessors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, inn, node)])
                ms.append(1)
            vs.append(varind['u_{}_{}'.format(k.ID, node)])
            ms.append(-1)
            prob.linear_constraints.add([cplex.SparsePair(vs, ms)],
                                        rhs=[0], senses='G')

        # eq 8
        for node in G.nodes_iter():
            # part 1 of eq8
            vs = []
            ms = []
            for out in G.successors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, node, out)])
                ms.append(1)
            prob.linear_constraints.add([cplex.SparsePair(vs, ms)],
                                        rhs=[1], senses='L')

            # part 2 of eq8
            vs = []
            ms = []
            for inn in G.predecessors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, inn, node)])
                ms.append(1)
            prob.linear_constraints.add([cplex.SparsePair(vs, ms)],
                                        rhs=[1], senses='L')
        # eq 10
        rhs = apps['Panopticon']['tcamcapacity']
        for node in G.nodes_iter():
            vs = []
            ms = []
            # for k in commodities:

            for out in G.successors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, node, out)])
                ms.append(1)

            for inn in G.predecessors(node):
                vs.append(varind['x_{}_{}_{}'.format(k.ID, inn, node)])
                ms.append(1)
            prob.linear_constraints.add([cplex.SparsePair(vs, ms)],
                                        rhs=[rhs], senses='L')

    d = {}
    for name in prob.variables.get_names():
        if name.startswith('x_'):
            d[varind[name]] = 1
    prob.objective.set_linear(d.iteritems())
    prob.objective.set_sense(prob.objective.sense.minimize)

    return prob

