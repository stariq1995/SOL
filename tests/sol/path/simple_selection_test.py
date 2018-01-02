# coding=utf-8
import hypothesis
import numpy
import pytest
import sys
import tmgen
from hypothesis import example
from hypothesis import given
from hypothesis import strategies as st
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.path.select import k_shortest_paths, choose_rand
from sol.topology.provisioning import traffic_classes
from sol.utils.ph import listeq

from sol.topology.generators import complete_topology


@pytest.fixture(scope='module')
def pptc():
    """
    An example paths per traffic class
    """
    # get a complete topology
    topo = complete_topology(5)
    # generate a dummy TM and traffic classes
    tm = tmgen.uniform_tm(5, 20, 50, 1)
    tc = traffic_classes(tm, {u'all': 1}, as_dict=False)
    # generate all possibe paths
    res = generate_paths_tc(topo, tc, null_predicate, 10, numpy.inf)
    return res


# Set shortest selection with a variety of values, including one example value
@given(num=st.integers(min_value=0, max_value=1<<31-1))
@example(num=4)
def test_shortest(pptc, num):
    """Check shortest path selection"""
    k_shortest_paths(pptc, num)
    # ensure correct number of paths, for different ways of checking the size
    for tc in pptc.tcs():
        expected = min(num, pptc.num_paths(tc, all=True))
        assert len(pptc.paths(tc)) == expected
        assert pptc.paths(tc).size == expected
        assert pptc.num_paths(tc) == expected
        assert pptc.num_paths(tc, False) == expected
    # ensure that the paths are actually shortest for explicit examples
    if num == 4:
        for tc in pptc.tcs():
            assert listeq(list(map(len, pptc.paths(tc))), [1, 2, 2, 2])


def random_test(pptc):
    """Check that paths chosen are random"""
    # Check number or chosen paths only
    # No good way to check their "randomness"
    choose_rand(pptc, 5)
    for tc in pptc.tcs():
        assert len(pptc.paths(tc)) == 5

