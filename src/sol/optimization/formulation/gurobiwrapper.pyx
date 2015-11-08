# coding=utf-8
from sol.optimization.formulation.optbase import Optimization
from gurobipy import *

class OptimizationGurobi(Optimization):

    def __init__(self):
        self.opt = Model()
        self.vars = dict()

    def addDesicionVars(self, pptc):
        cdef int pi
        for tc in pptc:
            for pi in xrange(len(pptc)):
                name = self.xp(tc, pi)
                self.vars[name] = self.opt.addVar(ub=1, name=name)
        self.opt.update()

    def allocateFlow(self, pptc, allocation=None):
        cdef int pi
        for tc in pptc:
            self.opt.addVar(ub=1, name=self.al(tc))
        if allocation is None:
            pass
        else:
            pass
            # self.opt.addConstr(,GRB.EQUAL, allocation, name='Allocation.')

    def linkCap(self):
        pass

    def routeAll(self):
        pass

    def setTimeLimit(self, long time):
        self.opt.params.TimeLimit = time
        self.opt.update()

    def solve(self):
        self.opt.optimize()

    def write(self, fname):
        self.opt.write(fname + ".lp")

    def writeSolution(self, fname):
        self.write(fname + ".sol")