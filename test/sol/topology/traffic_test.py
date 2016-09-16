# coding=utf-8

import pytest
import copy
from sol.topology.traffic import TrafficClass


def test_traffic_class():
    t = TrafficClass(1, 'web', 1, 2)
    t2 = TrafficClass(2, 'web', 1, 2)
    t3 = TrafficClass(1, 'ssh', 2, 1)
    assert t == t
    assert copy.copy(t) == t
    assert t != t3
    assert t != t2
    assert t.getIEPair() == (1, 2)
    assert str(t) == 'TrafficClass 1 -> 2, web, ID=1'
    with pytest.raises(AttributeError):
        print t3.myval
    assert t != 'randomstring'
    assert not t == 'randomlkdjf;aljkd'

    # TODO: include tests for other members: mainly IP prefixes and ports