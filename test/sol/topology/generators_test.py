# coding=utf-8
import networkx

from sol.topology.topologynx import Topology
from sol.topology.generators import complete_topology, chain_topology, \
    fat_tree, CORE_LAYER
from sol.utils.const import SWITCH, CORE_LAYER


def test_generators():
    """
    Some basic test for topology generators. Ensure we return correct types
    and correct number of nodes.
    """
    topo = complete_topology(5)
    assert isinstance(topo, Topology)
    assert isinstance(topo.get_graph(), networkx.DiGraph)
    assert topo.num_nodes() == 5
    assert networkx.is_isomorphic(topo.get_graph().to_undirected(),
                                  networkx.complete_graph(5))

    topo = chain_topology(10)
    assert isinstance(topo, Topology)
    assert isinstance(topo.get_graph(), networkx.DiGraph)
    assert networkx.is_isomorphic(topo.get_graph().to_undirected(),
                                  networkx.path_graph(10))


def test_fattree_generator():
    """
    Some basic test for FatTree generator. Ensure we return correct types
    and correct number of nodes. Additionally, check that core has correct
    number of switches and fatter links
    """
    topo = fat_tree(8)
    assert isinstance(topo, Topology)
    assert isinstance(topo.get_graph(), networkx.DiGraph)
    # correct size
    assert topo.num_nodes() == 80
    G = topo.get_graph()
    # every node has a layer attribute
    assert all([u'layer' in G.node[n] for n in G.nodes_iter()])
    # there are correct number of core switches
    len([n for n in G.nodes_iter() if G.node[n][u'layer'] == CORE_LAYER]) == 16
    assert all([u'capacitymult' in G.edge[u][v] for u, v in G.edges_iter()])


def test_switch_labels():
    """
    Ensure that switches are labeled appropriately

    """
    topo = complete_topology(5)
    for node in topo.nodes():
        assert SWITCH in topo.get_service_types(node)
