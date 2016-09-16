# coding=utf-8

import sol.utils.ph as ph
from sol.utils.ph import tup2str


def testConverters():
    assert tup2str((1, 2, 'hi')) == '1_2_hi'


def testlisteq():
    assert ph.listeq([1], [1])
    assert ph.listeq([], [])
    assert ph.listeq([2, 2, 2, 2], [2, 2, 2, 2])
    assert ph.listeq([1], [0x1])
    assert not ph.listeq([1], [1, 1])
    assert not ph.listeq([2, 3, 4], [0, 2, 3, 4])
    assert not ph.listeq([2, 3, 4], [1, 3, 4])
