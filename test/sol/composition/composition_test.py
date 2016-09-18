# coding=utf-8

import pytest

from sol.opt.app import App
from sol.opt.composer import _detect_cost_conflict, CompositionError


def test_ResourceConflictDetection():
    a1 = App({}, [], {'r1': 200, 'r2': 300})
    a2 = App({}, [], {'r1': 200, 'r2': 300, 'r3': 500})
    _detect_cost_conflict([a1, a2])
    _detect_cost_conflict([a1])
    _detect_cost_conflict([])
    # with pytest.raises(TypeError):
    #     _detect_cost_conflict({})
    a1 = App({}, [], {'r1': 200, 'r2': 300})
    a2 = App({}, [], {'r1': 200, 'r2': 1, 'r3': 500})
    with pytest.raises(CompositionError):
        _detect_cost_conflict([a1, a2])