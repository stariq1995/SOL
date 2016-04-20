# coding=utf-8
import os

import pytest

from sol.path.paths import Path, PathWithMbox


def testPathGetters():
    p = Path([1, 4, 6, -1])
    p2 = PathWithMbox([1, 4, 6, -1], [4, 6])
    assert p.getFlowFraction() == 0
    assert p.getIngress() == 1
    assert p.getEgress() == -1
    assert p.getIEPair() == (1, -1)
    assert p.getNodes() == [1, 4, 6, -1]
    # assert p.getNodesAsTuple() == (1, 4, 6, -1)
    assert list(p.getLinks()) == [(1, 4), (4, 6), (6, -1)]

    # test indexing/length
    assert p[1] == 4
    assert p[-1] == -1
    assert len(p) == 4
    assert len(p2) == 4
    assert p2.fullLength() == 6

    # test the __contains__ method
    assert 6 in p
    assert 7 not in p
    assert 4 in p2 and -1 in p2
    assert not 4 not in p


def testPathEquality():
    p = Path([1, 2, 3, 4])
    p1 = Path([1, 2, 3, 4], flowFraction=10)
    p2 = Path([1, 2, 3, 5])

    p3 = PathWithMbox([1, 2, 3, 4], [2])
    p4 = PathWithMbox([1, 2, 3, 4], [2, 4])
    p5 = PathWithMbox([1, 2, 3, 4], [2, 4], flowFraction=100)
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
    assert not p == (1, 2, 3, 4)

    # wrong operators must raise and exception:
    with pytest.raises(TypeError):
        p4 < p3
    with pytest.raises(TypeError):
        p > p2
    with pytest.raises(TypeError):
        p <= p2
    with pytest.raises(TypeError):
        p >= p2


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


def testPathEncoding():
    p = Path([1, 2, 3])
    assert p.encode() == {'nodes': [1, 2, 3], 'numFlows': 0}
    assert p == p.decode(p.encode())
    try:
        import msgpack
        l = msgpack.loads(msgpack.dumps(p, default=lambda x: x.encode()),
                          object_hook=Path.decode)
        assert p == l
    except ImportError:
        pass


@pytest.mark.skipif('TRAVIS' in os.environ,
                    reason='Travis CI has old version of py.test with to warning tests')
def testPathWarn():
    with pytest.warns(UserWarning):
        p = Path([1])


def testPathWithMboxEncoding():
    p = PathWithMbox([1, 2, 3], useMBoxes=[2])
    assert p.encode() == {'nodes': [1, 2, 3], 'numFlows': 0, 'useMBoxes': [2], 'PathWithMbox': True}
    l = p.decode(p.encode())
    assert p == l

