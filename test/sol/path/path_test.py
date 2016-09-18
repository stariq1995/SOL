# coding=utf-8
import os

import pytest
from sol.path.paths import Path, PathWithMbox
from sol.utils.ph import listeq


@pytest.fixture(scope='module')
def apath():
    return Path([1, 9, 7, 3], 0)


def test_path_getters():
    p = Path([1, 4, 6, -1])
    p2 = PathWithMbox([1, 4, 6, -1], [4, 6])
    assert p.flow_fraction() == 0
    assert p.ingress() == 1
    assert p.egress() == -1
    assert p.iepair() == (1, -1)
    assert listeq(p.nodes(), [1, 4, 6, -1])
    assert listeq(list(p.links()), [(1, 4), (4, 6), (6, -1)])

    # test indexing/length
    assert p[1] == 4
    assert p[-1] == -1
    # Length should be number of hops, not number of nodes
    assert len(p) == 3
    assert len(p2) == 3

    # test the __contains__ method
    assert 6 in p
    assert 7 not in p
    assert 4 in p2 and -1 in p2
    assert not 4 not in p

    # test path setters
    with pytest.raises(TypeError):
        p[1] = 27


def test_path_equality():
    p = Path([1, 2, 3, 4])
    p1 = Path([1, 2, 3, 4], flow_fraction=10)
    p2 = Path([1, 2, 3, 5])

    p3 = PathWithMbox([1, 2, 3, 4], [2])
    p4 = PathWithMbox([1, 2, 3, 4], [2, 4])
    p5 = PathWithMbox([1, 2, 3, 4], [2, 4], flow_fraction=100)
    # flow_fraction on the path does not matter when testing equality
    assert p == p1
    # Path with different nodes are not equal
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


# At this point paths are not hashable
# def testPathHashing():
#     d = {}
#     p = Path([1, 2, 3, 4])
#     p2 = PathWithMbox([1, 2, 3, 4], [2])
#     p3 = PathWithMbox([1, 2, 3, 4], [2, 4])
#     d[p] = 1
#     d[p2] = 2
#     assert len(d) == 2
#     d[p3] = 2
#     d[p] = 100
#     assert len(d) == 3
#     assert d[p] == 100


def test_uses_box():
    p2 = PathWithMbox([1, 4, 6, -1], [4, 6])
    assert p2.uses_box(4)
    assert p2.uses_box(6)
    assert not p2.uses_box(1)


def test_path_encoding(apath):
    d = apath.encode()
    assert u'nodes' in d
    assert d[u'type'] == u'Path'
    assert u'flow_fraction' in d
    assert u'id' in d
    assert apath == Path.decode(apath.encode())


@pytest.mark.skipif('TRAVIS' in os.environ,
                    reason='Travis CI has old version of py.test with to '
                           'warning tests')
def test_path_warn():
    with pytest.warns(UserWarning):
        p = Path([1])


def test_pathmbox_encoding():
    p = PathWithMbox([1, 2, 3], use_mboxes=[2])
    d = p.encode()
    assert u'nodes' in d
    assert d[u'type'] == u'PathWithMBox'
    assert u'flow_fraction' in d
    assert u'id' in d
    assert listeq(d[u'use_mboxes'], [2])
    l = p.decode(p.encode())
    assert p == l
