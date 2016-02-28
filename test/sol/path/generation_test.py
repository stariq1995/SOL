# coding=utf-8
import pytest

from sol.path import PathWithMbox
from sol.path import generatePathsPerIE
from sol.path.predicates import nullPredicate, useMboxModifier
from sol.topology.generators import generateChainTopology, \
    generateCompleteTopology
from sol.utils.exceptions import NoPathsException


def test_pathgen_simple():
    """
    Check that one path is found on chain topology
    """
    chaintopo = generateChainTopology(5)
    for sink in xrange(1, 5):
        pptc = generatePathsPerIE(0, sink, chaintopo, nullPredicate, cutoff=100)
        print pptc
        assert len(pptc) == 1

    with pytest.raises(NoPathsException):
        generatePathsPerIE(0, 4, chaintopo, lambda p, t: False, 100)

    chaintopo.getGraph().remove_edge(1, 2)
    with pytest.raises(NoPathsException):
        generatePathsPerIE(0, 4, chaintopo, nullPredicate, 100)
    assert len(generatePathsPerIE(0, 4, chaintopo, nullPredicate, cutoff=100,
                                  raiseOnEmpty=False)) == 0


def test_pathgen_cutoffs():
    t = generateCompleteTopology(8)
    pptc = generatePathsPerIE(1, 3, t, nullPredicate, 100)
    assert len(pptc) > 20
    pptc = generatePathsPerIE(1, 3, t, nullPredicate, 1)
    assert len(pptc) == 1
    pptc = generatePathsPerIE(1, 3, t, nullPredicate, 2)
    assert len(pptc) == 7
    pptc = generatePathsPerIE(1, 3, t, nullPredicate, 100, maxPaths=4)
    assert len(pptc) == 4


def test_pathgen_mbox():
    t = generateCompleteTopology(8)

    # noinspection PyUnusedLocal
    def mbox(path, ind, topology):
        return [PathWithMbox(path, [n], ind) for n in path]

    pptc = generatePathsPerIE(1, 3, t, nullPredicate, 2,
                              modifyFunc=mbox)
    assert len(pptc) == 20

    t.setMbox(1)
    t.setMbox(3)
    pptc = generatePathsPerIE(1, 3, t, nullPredicate, 2,
                              modifyFunc=useMboxModifier)
    assert len(pptc) == 14
