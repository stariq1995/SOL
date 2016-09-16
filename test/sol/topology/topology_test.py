# coding=utf-8
import os

import networkx

from sol.topology.topologynx import Topology
from sol.topology.generators import complete_topology
from sol.utils.const import SWITCH


def testTopologyWriteRead(tmpdir):
    dirname = os.path.abspath(tmpdir.dirname)
    topo = complete_topology(5)
    topo.to_graphml(dirname)
    topo2 = Topology(topo.name)
    topo2.loadGraph(dirname + os.path.sep + topo.name + '.graphml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.getGraph())
    topo.to_graphml(dirname, 'lalala.graphml')
    topo2.loadGraph(dirname + os.path.sep + 'lalala.graphml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.getGraph())


def testTopologyConstructor():
    # todo: test constructor with diff types
    pass


def testGetNumNodes():
    topo = complete_topology(8)
    assert topo.num_nodes() == 8
    assert topo.num_nodes(SWITCH) == 8
    assert topo.num_nodes('blah') == 0


def testServiceTypes():
    # todo: test code that deals with service types & middleboxes
    pass
