# coding=utf-8
import os

import networkx

from sol.topology.topology import Topology
from sol.topology.generators import complete_topology


def testTopologyWriteRead(tmpdir):
    dirname = os.path.abspath(tmpdir.dirname)
    topo = complete_topology(5)
    topo.write_graph(dirname)
    topo2 = Topology(topo.name)
    topo2.loadGraph(dirname + os.path.sep + topo.name + '.graphml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.getGraph())
    topo.write_graph(dirname, 'lalala.graphml')
    topo2.loadGraph(dirname + os.path.sep + 'lalala.graphml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.getGraph())


def testTopologyConstructor():
    # todo: test constructor with diff types
    pass


def testGetNumNodes():
    topo = complete_topology(8)
    assert topo.num_nodes() == 8
    assert topo.num_nodes('switch') == 8
    assert topo.num_nodes('middlebox') == 0


def testServiceTypes():
    # todo: test code that deals with service types & middleboxes
    pass
