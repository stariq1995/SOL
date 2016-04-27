# coding=utf-8
import pytest

import sol.utils.pythonHelper as ph
from sol.utils.pythonHelper import tup2str, str2tup


def testConverters():
    assert tup2str((1, 2, 'hi')) == '1_2_hi'
    assert str2tup('3_4') == ('3', '4')


# def testOneDict():
#     d = ph.alwaysOneDict()
#     assert d[1] == 1
#     assert d[2] == 1
#     assert d['hidhf'] == 1
#     with pytest.raises(TypeError):
#         d[2] = -1
#     assert d[2] == 1


def testListEq():
    assert ph.listEq([1], [1])
    assert ph.listEq([], [])
    assert ph.listEq([2, 2, 2, 2], [2, 2, 2, 2])
    assert ph.listEq([1], [0x1])
    assert not ph.listEq([1], [1, 1])
    assert not ph.listEq([2, 3, 4], [0, 2, 3, 4])
    assert not ph.listEq([2, 3, 4], [1, 3, 4])
