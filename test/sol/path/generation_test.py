# coding=utf-8
from __future__ import print_function

import pytest
from six.moves import xrange
from sol.path.generate import generate_paths_ie
from sol.path.paths import PathWithMbox
from sol.path.predicates import null_predicate, has_mbox_predicate
from sol.topology.generators import chain_topology, \
    complete_topology
from sol.utils.exceptions import NoPathsException


def test_pathgen_simple():
    """
    Check that one path is found on chain topology
    """
    chaintopo = chain_topology(5)
    for sink in xrange(1, 5):
        pptc = generate_paths_ie(0, sink, chaintopo, null_predicate, cutoff=100)
        print(pptc)
        assert len(pptc) == 1

    with pytest.raises(NoPathsException):
        generate_paths_ie(0, 4, chaintopo, lambda p, t: False, 100)

    chaintopo.get_graph().remove_edge(1, 2)
    with pytest.raises(NoPathsException):
        generate_paths_ie(0, 4, chaintopo, null_predicate, 100)
    assert len(generate_paths_ie(0, 4, chaintopo, null_predicate, cutoff=100,
                                 raise_on_empty=False)) == 0


def test_pathgen_cutoffs():
    t = complete_topology(8)
    pptc = generate_paths_ie(1, 3, t, null_predicate, 100)
    assert len(pptc) > 20
    pptc = generate_paths_ie(1, 3, t, null_predicate, 1)
    assert len(pptc) == 1
    pptc = generate_paths_ie(1, 3, t, null_predicate, 2)
    assert len(pptc) == 7
    pptc = generate_paths_ie(1, 3, t, null_predicate, 100, max_paths=4)
    assert len(pptc) == 4


def test_pathgen_mbox():
    t = complete_topology(8)

    # noinspection PyUnusedLocal
    def mbox(path, ind, topology):
        return [PathWithMbox(path, [n], ind) for n in path]

    pptc = generate_paths_ie(1, 3, t, null_predicate, 2,
                             modify_func=mbox)
    assert len(pptc) == 20

    t.set_mbox(1)
    t.set_mbox(3)
    pptc = generate_paths_ie(1, 3, t, null_predicate, 2,
                             modify_func=mbox)
    assert len(pptc) == 14
