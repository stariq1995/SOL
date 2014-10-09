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
    assert networkx.is_isomorphic(topo, topo2)
    topo.writeGraph(dirname, 'lalala')
    topo2 = Topology.loadGraph(dirname + os.path.sep + 'lalala.graphml')
    assert networkx.is_isomorphic(topo, topo2)

#todo: test constructor with diff types
#todo: test get numnodes


