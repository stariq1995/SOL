# coding=utf-8
import os

import networkx

from sol.topology import Topology
from sol.topology.generators import generateCompleteTopology


def testTopologyWriteRead(tmpdir):
    dirname = os.path.abspath(tmpdir.dirname)
    topo = generateCompleteTopology(5)
    topo.writeGraph(dirname)
    topo2 = Topology(topo.name)
    topo2.loadGraph(dirname + os.path.sep + topo.name + '.graphml')
    assert networkx.is_isomorphic(topo.getGraph(), topo2.getGraph())
    topo.writeGraph(dirname, 'lalala.graphml')
    topo2.loadGraph(dirname + os.path.sep + 'lalala.graphml')
    assert networkx.is_isomorphic(topo.getGraph(), topo2.getGraph())


def testTopologyConstructor():
    # todo: test constructor with diff types
    pass


def testGetNumNodes():
    topo = generateCompleteTopology(8)
    assert topo.getNumNodes() == 8
    assert topo.getNumNodes('switch') == 8
    assert topo.getNumNodes('middlebox') == 0

def testServiceTypes():
    # todo: test code that deals with service types & middleboxes
    pass