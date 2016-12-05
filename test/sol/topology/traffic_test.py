# coding=utf-8

import pytest
import copy

from sol.topology.traffic import TrafficClass


def test_traffic_class():
    # Check for getters correctness and sets equivalence of traffic classes
    t = TrafficClass(1, u'web', 1, 2)
    t2 = TrafficClass(2, u'web', 1, 2)
    t3 = TrafficClass(1, u'ssh', 2, 1)
    t4 = TrafficClass(1, u'web', 1, 2)
    assert t == t
    assert t == t4
    assert copy.copy(t) == t
    assert t != t3
    assert t != t2
    assert t.iepair() == (1, 2)
    assert str(t) == u'TrafficClass 1 -> 2, web, ID=1'
    with pytest.raises(AttributeError):
        print (t3.myval)
    assert t != u'randomstring'
    assert not t == u'randomlkdjf;aljkd'

    # TODO: include tests for other members: mainly IP prefixes and ports