# coding=utf-8
import networkx
import os
from sol.optimization.topology.generators import generateCompleteTopology
from sol.optimization.topology.topology import Topology


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
    #todo: test constructor with diff types
    pass

def testGetNumNodes():
    topo = generateCompleteTopology(8)
    assert topo.getNumNodes() == 8
    assert topo.getNumNodes('switch') == 8
    assert topo.getNumNodes('middlebox') == 0
    #todo: test get numnodes


