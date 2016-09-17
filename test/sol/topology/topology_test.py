# coding=utf-8
import os

import networkx

from sol.topology.topologynx import Topology
from sol.topology.generators import complete_topology
from sol.utils.const import SWITCH
from six import u


def testTopologyWriteRead(tmpdir):
    dirname = u(os.path.abspath(tmpdir.dirname))
    topo = complete_topology(5)
    topo.write_graph(dirname + os.path.sep + u'testgml.gml')
    topo2 = Topology(topo.name)
    topo2.load_graph(dirname + os.path.sep + u'testgml.gml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.get_graph())
    topo.write_graph(dirname + os.path.sep + u'lalala.gml')
    topo2.load_graph(dirname + os.path.sep + u'lalala.gml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.get_graph())


def testGetNumNodes():
    topo = complete_topology(8)
    assert topo.num_nodes() == 8
    assert topo.num_nodes(SWITCH) == 8
    assert topo.num_nodes(u'blah') == 0


def testServiceTypes():
    # todo: test code that deals with service types & middleboxes
    pass
