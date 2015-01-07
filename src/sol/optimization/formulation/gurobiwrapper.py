# coding=utf-8
from sol.optimization.formulation.optbase import Optimization

class OptimizationGurobi(Optimization):
    def addNodeCapacityPerPathConstraint(self, pptc, resource, nodecaps, nodeCapFunction):
        pass
    # TODO: implement Gurobi wrapper

    def __init__(self):
        raise NotImplementedError()