# coding=utf-8

"""
Utility module, implements functions that generate some basic topologies.
"""

import itertools

import networkx as nx
from six.moves import xrange
from sol.topology.topologynx import Topology

from sol.utils.const import SWITCH, CORE_LAYER, EDGE_LAYER, AGG_LAYER, ERR_ODD_ARITY


def fat_tree(k):
    """
    Creates a FatTree topology with a given '-arity'.

    .. seealso:: The `<ccr.sigcomm.org/online/files/p63-alfares.pdf>`_

    :param k: specify the k-value that controls the size of the topology
    :returns: the new topology
    :rtype: :py:class:`~sol.topology.topologynx.Topology`

    """
    assert k >= 0
    if k % 2 != 0:
        raise ValueError(ERR_ODD_ARITY)
    graph = nx.empty_graph()
    # Let's do the pods first
    index = 0
    bucket_size = int(k / 2)
    middle = []
    for pod in xrange(k):
        lower = xrange(index, index + bucket_size)
        index += bucket_size
        upper = xrange(index, index + bucket_size)
        index += bucket_size
        # Add upper and lower levels
        graph.add_nodes_from(lower, layer=EDGE_LAYER, functions=SWITCH)
        graph.add_nodes_from(upper, layer=AGG_LAYER, functions=SWITCH)
        # connect the levels
        graph.add_edges_from(itertools.product(lower, upper), capacitymult=1)
        # keep the upper level for later
        middle.extend(upper)
    # Now, create the core
    core = []
    for coreswitch in xrange(int((k ** 2) / 4)):
        graph.add_node(index, layer=CORE_LAYER, functions=SWITCH)
        core.append(index)
        index += 1
    graph.add_edges_from(itertools.product(core, middle), capacitymult=10)
    graph = graph.to_directed()
    return Topology(u'k{}'.format(k), graph)


def chain_topology(n, name=u'chain'):
    """
    Generates a chain topology.

    :param n: number of nodes in the chain
    :param name: name of the topology

    :return: the new topology
    :rtype: :py:class:`~sol.topology.topologynx.Topology`

    """
    assert n >= 0
    G = nx.path_graph(n).to_directed()
    t = Topology(name, G)
    return t


def complete_topology(n, name=u'complete'):
    """
    Generates a complete graph topology

    :param n: number of nodes in the complete graph
    :param name: name of the topology

    :return: the new topology
    :rtype: :py:class:`~sol.topology.topologynx.Topology`

    """
    assert n >= 0
    G = nx.complete_graph(n).to_directed()
    t = Topology(name, G)
    return t
