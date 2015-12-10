import pytest
from sol.utils.pythonHelper import tup2str, str2tup
import sol.utils.pythonHelper as ph

def testConverters():
    assert tup2str((1,2,'hi')) == '1_2_hi'
    assert str2tup('3_4') == ('3', '4')

def testOneDict():
    d = ph.alwaysOneDict()
    assert d[1] == 1
    assert d[2] == 1
    assert d['hidhf'] == 1
    with pytest.raises(TypeError):
        d[2] = -1
    assert d[2] == 1
