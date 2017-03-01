# coding=utf-8

import sol.utils.ph as ph
from sol.utils.ph import tup2str
from hypothesis import given
import hypothesis.strategies as st


def test_converters():
    """ Check that we convert a tuple to a string"""
    assert tup2str((1, 2, u'hi')) == u'1_2_hi'


def test_list_eq():
    """ Check that list equality function is working as intended"""
    assert ph.listeq([1], [1])
    assert ph.listeq([], [])
    assert ph.listeq([2, 2, 2, 2], [2, 2, 2, 2])
    assert ph.listeq([1], [0x1])
    assert not ph.listeq([1], [1, 1])
    assert not ph.listeq([2, 3, 4], [0, 2, 3, 4])
    assert not ph.listeq([2, 3, 4], [1, 3, 4])


def test_parse_bool():
    """Test our custom string to bool parser"""
    assert ph.parse_bool('true')
    assert ph.parse_bool('TRUE')
    assert not ph.parse_bool('false')
    assert not ph.parse_bool('FALSE')
    assert ph.parse_bool('yes')
    assert ph.parse_bool('yEs')
    assert ph.parse_bool('1')
    assert not ph.parse_bool('01')


@given(st.integers())
def test_noop(x):
    """Test the noop function"""
    assert ph.noop(x) == x
