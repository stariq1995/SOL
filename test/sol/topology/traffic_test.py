# coding=utf-8
import copy

import pytest

from sol.topology import *
from sol.utils.pythonHelper import listEq


def testTrafficClass():
    t = TrafficClass(1, 'web', 1, 2)
    t2 = TrafficClass(2, 'web', 1, 2)
    t3 = TrafficClass(1, 'ssh', 2, 1)
    assert t == t3
    assert t != t2
    assert t.getIEPair() == (1, 2)
    assert str(t) == 'Traffic class 1 -> 2, web, ID=1'
    with pytest.raises(AttributeError):
        print t3.myval
    t3.myval = 'val'
    assert t3.myval == 'val'
    t4 = TrafficClass(1, 'web', 1, 2, myval=20)
    assert t4.myval == 20
    assert t != 'randomstring'
    assert not t == 'randomlkdjf;aljkd'


def testTrafficMatrix():
    tm = TrafficMatrix({i: random.randint(0, 1e5) for i in xrange(1000)})
    tm2 = copy.deepcopy(tm)
    tm2.permute()
    assert len(tm) == len(tm2)
    assert tm.keys() == tm2.keys()
    assert not listEq(tm.values(), tm2.values())
    assert listEq(sorted(tm.values()), sorted(tm2.values()))
