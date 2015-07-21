# coding=utf-8

"""
Generates some basic topologies. Contains utility methods as well.
"""

import itertools

import networkx as nx

from sol.optimization.topology.topology import Topology

from sol.optimization.topology.extracttopo import ExtractTopo


def forceSwitchLabels(topology):
    """ Force all nodes to be labeled as switches

    :param topology: topology to operate on
    :return:
    """
    G = topology.getGraph()
    for n in G.nodes_iter():
        topology.addServiceType(n, 'switch')


def generateFatTree(k):
    """ Creates a FatTree topology as a directed graph

    :param k: specify the k-value that controls the size of the topology
    :returns: a ~:py:module:networkx DiGraph
    """
    G = nx.empty_graph()
    # Let's do the pods first
    index = 1
    middle = []
    for pod in xrange(k):
        lower = xrange(index, index + k / 2)
        index += k / 2
        upper = xrange(index, index + k / 2)
        index += k / 2
        # Add upper and lower levels
        G.add_nodes_from(lower, layer='edge', functions='switch')
        G.add_nodes_from(upper, layer='aggregation', functions='switch')
        # connect the levels
        G.add_edges_from(itertools.product(lower, upper), capacitymult=1)
        # keep the upper level for later
        middle.extend(upper)
    # Now, create the core
    core = []
    for coreswitch in xrange((k ** 2) / 4):
        G.add_node(index, layer='core', functions='switch')
        core.append(index)
        index += 1
    G.add_edges_from(itertools.product(core, middle), capacitymult=10)
    G = G.to_directed()
    return Topology('k{}'.format(k), G)


def generateChainTopology(n, name='chain'):
    """
    Generates a chain topology

    :param n: number of nodes in the chain
    :param name: name of the topology
    :return: the new topology
    :rtype TestTopology
    """
    G = nx.path_graph(n).to_directed()
    t = Topology(name, G)
    forceSwitchLabels(t)
    return t


def generateCompleteTopology(n, name='complete'):
    """
    Generates a complete graph topology

    :param n: number of nodes in the complete graph
    :param name: name of the topology
    :return: the new topology
    :rtype: TestTopology
    """
    G = nx.complete_graph(n).to_directed()
    t = Topology(name, G)
    forceSwitchLabels(t)
    return t

def extractTopo(controllerIP='localhost',name='onos-topo'):
    topo = ExtractTopo(controllerIp = controllerIP)
    G = topo.getGraph()#.to_directed()
    t = Topology(name,G)
    forceSwitchLabels(t)
    return t
	


