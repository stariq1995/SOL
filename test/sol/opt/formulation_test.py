import pytest

from sol.opt import OptimizationCPLEX, OptimizationGurobi
from sol.opt import getOptimization
from sol.utils.exceptions import InvalidConfigException

def test_getFunc():
    opt = getOptimization('cplex')
    assert isinstance(opt, OptimizationCPLEX)
    opt = getOptimization('CPlex')
    assert isinstance(opt, OptimizationCPLEX)
    opt = getOptimization('GuRobi')
    assert isinstance(opt, OptimizationGurobi)

    with pytest.raises(InvalidConfigException):
        opt = getOptimization('fakebackend')