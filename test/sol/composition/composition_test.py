# coding=utf-8
import pytest

from sol.opt.app import App
from sol.opt.composer import detectCostConflict, CompositionError


def test_ResourceConflictDetection():
    a1 = App({}, [], {'r1': 200, 'r2': 300})
    a2 = App({}, [], {'r1': 200, 'r2': 300, 'r3': 500})
    detectCostConflict([a1, a2])
    detectCostConflict([a1])
    detectCostConflict([])
    with pytest.raises(TypeError):
        detectCostConflict({})
    a1 = App({}, [], {'r1': 200, 'r2': 300})
    a2 = App({}, [], {'r1': 200, 'r2': 1, 'r3': 500})
    with pytest.raises(CompositionError):
        detectCostConflict([a1, a2])