# coding=utf-8
import pytest
from sol.optimization.path.generate import generatePathsPerIE
from sol.optimization.path.predicates import nullPredicate
from sol.optimization.topology.generators import generateChainTopology
from sol.util.exceptions import NoPathsException


def test_pathgen_simple():
    """
    Check that one path is found on chain topology
    """
    chaintopo = generateChainTopology(5)
    for sink in xrange(1, 5):
        ppk = generatePathsPerIE(0, sink, chaintopo,
                                 nullPredicate, cutoff=100)
        print ppk
        assert len(ppk) == 1

    chaintopo.getGraph().remove_edge(1, 2)
    with pytest.raises(NoPathsException):
        generatePathsPerIE(0, 4, chaintopo, nullPredicate, cutoff=100)