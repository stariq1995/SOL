# coding=utf-8

"""
Implements functions that generate some basic topologies.
"""

import itertools

import networkx as nx
from sol.topology.topologynx import Topology
from six.moves import xrange


def fat_tree(k):
    """
    Creates a FatTree topology with a given '-arity'.

    .. seealso:: The `<ccr.sigcomm.org/online/files/p63-alfares.pdf>`_

    :param k: specify the k-value that controls the size of the topology
    :returns: a ~:py:module:`networkx.DiGraph`
    """
    graph = nx.empty_graph()
    # Let's do the pods first
    index = 0
    middle = []
    for pod in xrange(k):
        lower = xrange(index, index + k / 2)
        index += k / 2
        upper = xrange(index, index + k / 2)
        index += k / 2
        # Add upper and lower levels
        graph.add_nodes_from(lower, layer='edge', functions='switch')
        graph.add_nodes_from(upper, layer='aggregation', functions='switch')
        # connect the levels
        graph.add_edges_from(itertools.product(lower, upper), capacitymult=1)
        # keep the upper level for later
        middle.extend(upper)
    # Now, create the core
    core = []
    for coreswitch in xrange((k ** 2) / 4):
        graph.add_node(index, layer='core', functions='switch')
        core.append(index)
        index += 1
    graph.add_edges_from(itertools.product(core, middle), capacitymult=10)
    graph = graph.to_directed()
    return Topology('k{}'.format(k), graph)


def chain_topology(n, name='chain'):
    """
    Generates a chain topology

    :param n: number of nodes in the chain
    :param name: name of the topology
    :return: the new topology
    :rtype :py:class:`sol.topology.topologynx.Topology`
    """
    G = nx.path_graph(n).to_directed()
    t = Topology(name, G)
    return t


def complete_topology(n, name='complete'):
    """
    Generates a complete graph topology

    :param n: number of nodes in the complete graph
    :param name: name of the topology
    :return: the new topology
    :rtype: :py:class:`sol.topology.topologynx.Topology`
    """
    G = nx.complete_graph(n).to_directed()
    t = Topology(name, G)
    return t
