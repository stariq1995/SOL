# coding=utf-8

import copy

import pytest
from numpy import array
from sol.topology.traffic import TrafficClass


@pytest.fixture(scope='function')
def t():
    return TrafficClass(1, u'web', 1, 2)


@pytest.fixture(scope='function')
def t2():
    return TrafficClass(2, u'web', 1, 2)


@pytest.fixture(scope='function')
def t3():
    return TrafficClass(1, u'ssh', 2, 1)


def test_traffic_class_eq(t, t2, t3):
    """
    Checks traffic class equality. Traffic class ID is the only unique identifier
    of the class. This allows optimization to simplify some intertal logic by using
    vectorized operations across all traffic classes/paths/epochs
    """
    # Check for correctness of getters and equivalence of traffic classes
    assert t == t
    assert t == t3
    assert t != t2
    assert copy.copy(t) == t
    assert t != u'randomstring :)'
    assert t != 0
    assert t != ''
    assert t is not None


def test_traffic_class_hash(t, t2, t3):
    """
    Checks the implementation of traffic class hashing
    """
    d = {}
    # two classes should hash to the same instance
    d[t] = 0
    d[t3] = 3
    assert len(d) == 1  # thus len == 1
    assert d[t] == 3  # later value is correct

    # and finally check that the ID is what gets hashed
    t.name = 'abcdef'
    t.src = -900
    t.dst = 0
    t.volFlows = array([2000])
    d[t] = 90
    assert d[t3] == 90


def test_traffic_class_getters(t, t2, t3):
    """
    Ensure that we have i/e getters
    """
    assert t.iepair() == (1, 2)
    assert t.ingress() == 1
    assert t2.egress() == 2


def test_volume_masking():
    pass

# TODO: test encoding and decoding
