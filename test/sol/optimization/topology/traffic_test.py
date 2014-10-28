# coding=utf-8
import copy
import random
import pytest

from sol.optimization.topology.traffic import Path, PathWithMbox, \
    TrafficClass, TrafficMatrix


def testPathGetters():
    p = Path([1, 4, 6, -1])
    p2 = PathWithMbox([1, 4, 6, -1], [4, 6])
    assert p.getNumFlows() == 0
    assert p.getIngress() == 1
    assert p.getEgress() == -1
    assert p.getIEPair() == (1, -1)
    assert p.getNodes() == [1, 4, 6, -1]
    assert p.getNodesAsTuple() == (1, 4, 6, -1)
    assert list(p.getLinks()) == [(1, 4), (4, 6), (6, -1)]

    assert p[1] == 4
    assert p[-1] == -1
    assert len(p) == 4
    assert len(p2) == 4


def testPathEquality():
    p = Path([1, 2, 3, 4])
    p1 = Path([1, 2, 3, 4], 10)
    p2 = Path([1, 2, 3, 5])

    p3 = PathWithMbox([1, 2, 3, 4], [2])
    p4 = PathWithMbox([1, 2, 3, 4], [2, 4])
    p5 = PathWithMbox([1, 2, 3, 4], [2, 4], 100)
    # NumFlows does not matter
    assert p == p1
    # Different nodes are not equal
    assert p != p2
    assert p1 != p2

    # Different types of paths are not equal
    assert p != p3
    # Diff useMboxes are not equal
    assert p3 != p4
    assert p3 != p5
    # again, numflows does not matter
    assert p4 == p5


def testPathSetters():
    p = Path([1, 2, 3, 4])
    p.setNumFlows(100)
    assert p.getNumFlows() == 100
    # assert p._numFlows == 100


def testPathHashing():
    d = {}
    p = Path([1, 2, 3, 4])
    p2 = PathWithMbox([1, 2, 3, 4], [2])
    p3 = PathWithMbox([1, 2, 3, 4], [2, 4])
    d[p] = 1
    d[p2] = 2
    assert len(d) == 2
    d[p3] = 2
    d[p] = 100
    assert len(d) == 3
    assert d[p] == 100


def testUsesBox():
    p2 = PathWithMbox([1, 4, 6, -1], [4, 6])
    assert p2.usesBox(4)
    assert p2.usesBox(6)
    assert not p2.usesBox(1)


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

def testTrafficMatrix():
    tm = TrafficMatrix({(1, 2): 100, (3, 4): 500, (2, 4): 200})
    tm2 = copy.deepcopy(tm)
    r = random.Random(1)
    tm2.permute(rand=r.random)
    assert len(tm) == len(tm2)
    assert tm.keys() == tm2.keys()
    assert tm.values() != tm2.values()
    assert sorted(tm.values()) == sorted(tm2.values())