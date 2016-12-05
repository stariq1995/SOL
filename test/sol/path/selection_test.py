# coding=utf-8
import numpy
import pytest
import tmgen
from six import iteritems, itervalues
from six.moves import range
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.path.select import k_shortest_paths, choose_rand
from sol.topology.generators import complete_topology
from sol.topology.provisioning import traffic_classes


# paramertize with different topology sizes
@pytest.fixture(params=[5], scope='function')
def pptc(request):
    # get a complete topology
    topo = complete_topology(request.param)
    # generate a dummy TM and traffic classes
    tm = tmgen.uniform_tm(request.param, 20, 50, 1)
    tc = traffic_classes(tm, {u'all': 1}, {u'all': 10})
    # generate all possibe paths
    res = generate_paths_tc(topo, tc, null_predicate, 10, numpy.inf)
    return res


# of paths in place and not
def test_shortest(pptc):
    k_shortest_paths(pptc, 4)
    # ensure correct number of paths
    for tc in pptc:
        assert len(pptc.paths(tc)) == min(4, len(pptc[tc]))
        assert len(pptc[tc]) == min(4, len(pptc[tc]))
        assert pptc[tc].size == min(4, len(pptc[tc]))
    # ensure that the paths are actually shortest
    for tc in pptc:
        assert map(len, pptc.paths(tc)) == [1, 2, 2, 2]


def random_test(pptc):
    # Check number or chosen paths only
    # No good way to check their "randomness"
    choose_rand(pptc, 5)
    for tc in pptc:
        assert len(pptc.paths(tc)) == 5


# @pytest.mark.parametrize('inplace', [True, False])
# def test_sort(pptc, inplace):
#     if inplace:
#         sort_paths(pptc, inplace=inplace)
#     else:
#         pptc = sort_paths(pptc, inplace=inplace)
#     for paths in itervalues(pptc):
#         for i in range(len(paths) - 1):
#             assert len(paths[i]) <= len(paths[i + 1])
