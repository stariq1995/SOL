# coding=utf-8
import pytest
from sol.topology.provisioning import generateTrafficClasses, uniformTM

from sol.path.generate import generatePathsPerTrafficClass
from sol.path.select import k_shortest_paths, choose_rand
from sol.path.predicates import nullPredicate
from sol.topology.generators import complete_topology


@pytest.fixture
def pptc():
    topo = complete_topology(8)
    iePairs = [(0, 3)]
    tc = generateTrafficClasses(iePairs, uniformTM(iePairs, 1000), {'allTraffic': 1},
                                {'allTraffic': 10})
    pptc = generatePathsPerTrafficClass(topo, tc, nullPredicate, 100)
    return pptc


def testShortest(pptc):
    subset = k_shortest_paths(pptc, 5)
    # ensure correct number of paths
    for k, v in subset.iteritems():
        assert len(v) == 5
    # ensure that the paths are actually shortest
    for k, v in subset.iteritems():
        assert map(len, v) == [2, 3, 3, 3, 3]


def shortest_test_keyword(pptc):
    # check all keyword argument functionality.
    pass


def random_test(pptc):
    # Check number
    subset = choose_rand(pptc, 5)
    for k, v in subset.iteritems():
        assert len(v) == 5
        # check that all paths are unique
        assert len(set(v)) == 5
