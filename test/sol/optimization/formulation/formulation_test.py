import pytest
from sol.optimization.formulation import getOptimization, OptimizationGurobi
from sol.optimization.formulation import OptimizationCPLEX
from sol.utils.exceptions import InvalidConfigException

__author__ = 'victor'

def test_getFunc():
    opt = getOptimization('cplex')
    assert isinstance(opt, OptimizationCPLEX)
    opt = getOptimization('CPlex')
    assert isinstance(opt, OptimizationCPLEX)
    opt = getOptimization('GuRobi')
    assert isinstance(opt, OptimizationGurobi)

    with pytest.raises(InvalidConfigException):
        opt = getOptimization('fakebackend')