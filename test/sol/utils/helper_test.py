# coding=utf-8

import sol.utils.ph as ph
from sol.utils.ph import tup2str


def testConverters():
    assert tup2str((1, 2, u'hi')) == u'1_2_hi'


def testlisteq():
    assert ph.listeq([1], [1])
    assert ph.listeq([], [])
    assert ph.listeq([2, 2, 2, 2], [2, 2, 2, 2])
    assert ph.listeq([1], [0x1])
    assert not ph.listeq([1], [1, 1])
    assert not ph.listeq([2, 3, 4], [0, 2, 3, 4])
    assert not ph.listeq([2, 3, 4], [1, 3, 4])


def testparsebool():
    assert ph.parse_bool('true')
    assert ph.parse_bool('TRUE')
    assert not ph.parse_bool('false')
    assert not ph.parse_bool('FALSE')
    assert ph.parse_bool('yes')
    assert ph.parse_bool('yEs')
    assert ph.parse_bool('1')
    assert not ph.parse_bool('01')
