# coding=utf-8
from __future__ import print_function

import pytest
from six.moves import xrange
from sol.path.generate import generate_paths_ie, use_mbox_modifier
from sol.path.predicates import null_predicate, has_mbox_predicate
from sol.topology.generators import chain_topology, \
    complete_topology
from sol.utils.exceptions import NoPathsException
from sol.utils.ph import listeq


@pytest.fixture(scope='function')
def topo():
    """ A topology """
    return complete_topology(8)


def test_pathgen_simple():
    # Check that one path is found on the chain topology
    chaintopo = chain_topology(5)
    for sink in xrange(1, 5):
        pptc = generate_paths_ie(0, sink, chaintopo, null_predicate, cutoff=100)
        assert len(pptc) == 1

    # Exception should be raised because the predicate is False
    with pytest.raises(NoPathsException):
        generate_paths_ie(0, 4, chaintopo, lambda p, t: False, 100)

    # Now remove the topology edge, so no paths between 0 and 4
    chaintopo.get_graph().remove_edge(1, 2)
    # Check that exception is raised when no paths is found
    with pytest.raises(NoPathsException):
        generate_paths_ie(0, 4, chaintopo, null_predicate, 100)
    # If not exceptions to be thrown, length should be 0.
    assert len(generate_paths_ie(0, 4, chaintopo, null_predicate, cutoff=100,
                                 raise_on_empty=False)) == 0


def test_pathgen_cutoffs(topo):
    # check that cutoffs work as desired, without any predicates
    # All paths for long (>100) length
    paths = generate_paths_ie(1, 3, topo, null_predicate, 100)
    # for a topology of size n, number of paths is
    # 1 + \sum_{k=2}^{n-2} k! (n-2 choose k)
    assert len(paths) == 1957
    # only one path with length 1
    paths = generate_paths_ie(1, 3, topo, null_predicate, 1)
    assert len(paths) == 1
    assert listeq(paths[0].nodes(), [1, 3])
    # 7 paths of length 2 or 1 (1 from previous, and 8-2 other midpoints)
    paths = generate_paths_ie(1, 3, topo, null_predicate, 2)
    assert len(paths) == 7
    print (paths)
    # Test that length of each path is at most 2 since that was the cutoff
    assert max(map(len, paths)) == 2
    # check that max_paths works
    paths = generate_paths_ie(1, 3, topo, null_predicate, 100, max_paths=4)
    assert len(paths) == 4


def test_pathgen_mbox(topo):
    # This will just add another path --- a bogus "expansion" function
    def mbox(path, offset, topo):
        return [path, path]

    paths = generate_paths_ie(1, 3, topo, null_predicate, 1000,
                              modify_func=mbox)

    # for a topology of size n, number of paths is
    # 1 + \sum_{k=2}^{n-2} k! (n-2 choose k)
    # Except here it is twice that, because of the bogus expansion function
    assert len(paths) == 3914

    topo.set_mbox(1)
    topo.set_mbox(3)
    pptc = generate_paths_ie(1, 3, topo, null_predicate, 2,
                             modify_func=mbox)
    # Twice of the seven paths of length 2.
    assert len(pptc) == 14

    topo.set_mbox(1, False)
    topo.set_mbox(3, False)
    topo.set_mbox(2, True)
    topo.set_mbox(4, True)
    topo.set_mbox(5, True)
    # Test the modifier function in SOL
    paths = generate_paths_ie(1, 3, topo, has_mbox_predicate, 2,
                              modify_func=use_mbox_modifier)
    print (paths)
    # This should only return {3 choose 2} paths
    assert len(paths) == 3
