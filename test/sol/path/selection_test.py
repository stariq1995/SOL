# coding=utf-8

import pytest
import tmgen
from six import iteritems
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.path.select import k_shortest_paths, choose_rand
from sol.topology.generators import complete_topology
from sol.topology.provisioning import traffic_classes


# paramertize with different topology sizes
@pytest.fixture(params=[3, 5, 8])
def pptc(request):
    # get a complete topology
    topo = complete_topology(request.param)
    # generate a dummy TM and traffic classes
    tm = tmgen.uniform_iid(request.param, 20, 50, 1)
    tc = traffic_classes(tm, {u'all': 1}, {u'all': 10})
    # generate all possibe paths
    res = generate_paths_tc(topo, tc, null_predicate, 100, 100)
    return res


@pytest.mark.parametrize('inplace', [True, False])  # do this for both sorting
# of paths in place and not
def test_shortest(pptc, inplace):
    subset = k_shortest_paths(pptc, 5, inplace=inplace)
    # ensure correct number of paths
    for tc, paths in iteritems(subset):
        assert len(paths) == min(5, len(pptc[tc]))
    # ensure that the paths are actually shortest
    for tc, paths in iteritems(subset):
        print (map(len, paths))
        assert map(len, paths) == [2, 3, 3, 3, 3]


def random_test(pptc):
    # Check number or chosen paths only
    # No good way to check their "randomness"
    subset = choose_rand(pptc, 5)
    for tc, paths in iteritems(subset):
        assert len(paths) == 5
        # check that all paths are unique
        assert len(set(paths)) == 5
