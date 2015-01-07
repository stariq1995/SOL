from sol.optimization.formulation.optbase import Optimization

class OptimizationGurobi(Optimization):
    def addNodeCapacityIfActive(self, pptc, resource, nodecaps, nodeCapFunction):
        pass
    # TODO: implement Gurobi wrapper