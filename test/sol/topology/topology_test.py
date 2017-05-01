# coding=utf-8
import os

import networkx
import pytest
from hypothesis import assume
from hypothesis import given, strategies as st
from six import u
from sol.topology.topologynx import Topology

from sol.topology.generators import complete_topology
from sol.utils.const import SWITCH


def test_write_read(tmpdir):
    """Check that writing topology to disk and restoring it produces the expected result"""
    dirname = u(os.path.abspath(tmpdir.dirname))
    topo = complete_topology(5)
    for l in topo.links():
        topo.set_resource(l, 'myresource', 4)
    topo.write_graph(dirname + os.path.sep + u'testgml.gml')
    topo2 = Topology(topo.name)
    topo2.load_graph(dirname + os.path.sep + u'testgml.gml')
    assert networkx.is_isomorphic(topo.get_graph(), topo2.get_graph())
    assert topo.name == topo2.name

    # Check that resources are preserved
    for n in topo.nodes():
        assert topo.get_resources(n) == topo2.get_resources(n)
    for l in topo.links():
        assert topo.get_resources(n) == topo2.get_resources(n)


@given(st.integers(0, 100), st.text().filter(lambda x: x != SWITCH))
def test_num_nodes(size, some_text):
    """
    Check that num_nodes functions correctly regardless of topology size and service type
    :param size: size of the topology
    :param some_text: service type to test the absense of. So anything except 'switch'
    :return:
    """
    assume(some_text)
    topo = complete_topology(size)
    assert topo.num_nodes() == size  # size of the network
    assert topo.num_nodes(SWITCH) == size  # everyting is a switch
    assert topo.num_nodes(some_text) == 0  # no other functions present


def test_graph_directed():
    """
    Insure we keep newly constructed topologies as directed graph
    """
    topo = complete_topology(5)
    assert isinstance(topo.get_graph(), networkx.DiGraph)
    # even if original graph is undirected
    topo = Topology('noname', networkx.star_graph(8))
    assert topo.get_graph().is_directed()


@pytest.mark.skip()
def test_set_service_types():
    # todo: test code that deals with service types & middleboxes
    pass


# TODO: finish other topology tests
@pytest.mark.skip()
def test_set_resources():
    pass


@pytest.mark.skip()
def test_json_encode_decode():
    pass


@pytest.mark.skip()
def test_from_json():
    pass
