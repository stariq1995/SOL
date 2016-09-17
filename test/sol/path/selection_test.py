# coding=utf-8

import pytest
import tmgen
from sol.path.generate import generate_paths_ie, generate_paths_tc
from sol.path.predicates import null_predicate
from sol.path.select import k_shortest_paths, choose_rand
from sol.topology.generators import complete_topology
from sol.topology.provisioning import traffic_classes
from six import iteritems
from pprint import pprint


@pytest.fixture
def pptc():
    topo = complete_topology(8)
    tm = tmgen.uniform_iid(8, 20, 50, 1)
    tc = traffic_classes(tm, {u'all': 1}, {u'all': 10})
    res = generate_paths_tc(topo, tc, null_predicate, 100, 100)
    return res


def test_shortest(pptc):
    subset = k_shortest_paths(pptc, 5)
    pprint (subset)
    # ensure correct number of paths
    for k, v in iteritems(subset):
        assert len(v) == 5
    # ensure that the paths are actually shortest
    for k, v in iteritems(subset):
        print (v)
        assert map(len, v) == [2, 3, 3, 3, 3]


def random_test(pptc):
    # Check number
    subset = choose_rand(pptc, 5)
    for k, v in iteritems(subset):
        assert len(v) == 5
        # check that all paths are unique
        assert len(set(v)) == 5
