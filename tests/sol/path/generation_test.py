# coding=utf-8
from __future__ import print_function

import types

import pytest
from six.moves import xrange
from sol.path.generate import generate_paths_ie, use_mbox_modifier
from sol.path.predicates import null_predicate, has_mbox_predicate

from sol import Path
from sol import PathWithMbox
from sol.topology.generators import chain_topology, \
    complete_topology
from sol.utils.exceptions import NoPathsException
from sol.utils.ph import listeq


@pytest.fixture(scope='function')
def topo():
    return complete_topology(8)


def test_pathgen_simple():
    # Check that one path is found on the chain topology
    chaintopo = chain_topology(5)
    for sink in xrange(1, 5):
        paths = generate_paths_ie(0, sink, chaintopo, null_predicate, 10)
        assert len(list(paths)) == 1

    # Exception should be raised because the predicate is False
    def pf(p, t):
        return False
    # print (list(generate_paths_ie(0, 4, chaintopo, pf, 100)))
    with pytest.raises(NoPathsException):
        list(generate_paths_ie(0, 4, chaintopo, pf, 100))

    # Now remove the topology edge, so no paths between 0 and 4
    chaintopo.get_graph().remove_edge(1, 2)
    # Check that exception is raised when no paths is found
    with pytest.raises(NoPathsException):
        list(generate_paths_ie(0, 4, chaintopo, null_predicate, 100))
    # If not exceptions to be thrown, length should be 0.
    assert len(list(generate_paths_ie(0, 4, chaintopo, null_predicate, 100,
                                      raise_on_empty=False))) == 0


def test_pathgen_cutoffs(topo):
    # check that cutoffs work as desired, without any predicates
    # All paths for long (>100) length
    paths = list(generate_paths_ie(1, 3, topo, null_predicate, 100))
    # for a topology of size n, number of paths is
    # 1 + \sum_{k=2}^{n-2} k! (n-2 choose k)
    assert len(paths) == 1957
    # ensure that all paths have no flow (also sometimes catches wrong order constructor arguments)
    assert all([p.flow_fraction() == 0 for p in paths])
    # only one path with length 1
    paths = list(generate_paths_ie(1, 3, topo, null_predicate, 1))
    assert len(paths) == 1
    assert listeq(paths[0].nodes(), [1, 3])
    # 7 paths of length 2 or 1 (1 from previous, and 8-2 other midpoints)
    paths = list(generate_paths_ie(1, 3, topo, null_predicate, 2))
    assert len(paths) == 7
    # Test that length of each path is at most 2 since that was the cutoff
    assert max(map(len, paths)) == 2
    # check that max_paths works
    paths = list(generate_paths_ie(1, 3, topo, null_predicate, 100, max_paths=4))
    assert len(paths) == 4


def test_pathgen_mbox(topo):
    # This will just add another path --- a bogus "expansion" function
    def dummy_expansion(path, topo):
        return [Path(path), Path(path)]

    paths = list(generate_paths_ie(1, 3, topo, null_predicate, 1000,
                                   modify_func=dummy_expansion))

    # for a topology of size n, number of paths is
    # 1 + \sum_{k=2}^{n-2} k! (n-2 choose k)
    # Except here it is twice that, because of the bogus expansion function
    assert len(paths) == 3914
    # ensure that all paths have no flow (also sometimes catches wrong order constructor arguments)
    assert all([p.flow_fraction() == 0 for p in paths])

    topo.set_mbox(1)
    topo.set_mbox(3)
    pptc = list(generate_paths_ie(1, 3, topo, null_predicate, 2,
                                  max_paths=float('inf'),
                                  modify_func=dummy_expansion))
    # Twice of the seven paths of length 2.
    assert len(pptc) == 14
    assert all([p.flow_fraction() == 0 for p in paths])

    topo.set_mbox(1, False)
    topo.set_mbox(3, False)
    topo.set_mbox(2, True)
    topo.set_mbox(4, True)
    topo.set_mbox(5, True)
    # Test the modifier function in SOL
    paths = list(generate_paths_ie(1, 3, topo, has_mbox_predicate, 2,
                                   modify_func=use_mbox_modifier))
    # This should only return {3 choose 2} paths
    assert len(paths) == 3
    assert all([p.flow_fraction() == 0 for p in paths])
    assert all([isinstance(p, PathWithMbox) for p in paths])
