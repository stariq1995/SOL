# coding=utf-8
import networkx

from sol.topology.topology import Topology
from sol.topology.generators import generateCompleteTopology, generateChainTopology, generateFatTree, forceSwitchLabels


def testGenerators():
    """
    Some basic test for topology generators. Ensure we return correct types
    and correct number of nodes.
    """
    topo = generateCompleteTopology(5)
    assert isinstance(topo, Topology)
    assert isinstance(topo.getGraph(), networkx.DiGraph)
    assert topo.getNumNodes() == 5

    topo = generateChainTopology(10)
    assert isinstance(topo, Topology)
    assert isinstance(topo.getGraph(), networkx.DiGraph)


def testFatTreeGenerator():
    """
    Some basic test for FatTree generator. Ensure we return correct types
    and correct number of nodes. Additionally, check that core has correct
    number of switches and fatter links
    """
    topo = generateFatTree(8)
    assert isinstance(topo, Topology)
    assert isinstance(topo.getGraph(), networkx.DiGraph)
    # correct size
    assert topo.getNumNodes() == 80
    G = topo.getGraph()
    # every node has a layer attribute
    assert all(['layer' in G.node[n] for n in G.nodes_iter()])
    # there are correct number of core switches
    len([n for n in G.nodes_iter() if G.node[n]['layer'] == 'core']) == 16
    assert all(['capacitymult' in G.edge[u][v] for u, v in G.edges_iter()])


def testForceSwitchLabels():
    """
    Ensure that switches are labeled appropriately

    """
    topo = generateCompleteTopology(5)
    forceSwitchLabels(topo)
    G = topo.getGraph()
    for node in G.nodes_iter():
        assert 'switch' in G.node[node]['services']
