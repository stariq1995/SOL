# coding=utf-8
from __future__ import division

from collections import defaultdict

import networkx as nx
from gurobipy import *

from sol.optimization.formulation.optbase import Optimization
from sol.utils.exceptions import FormulationException
from sol.utils.pythonHelper import tup2str
from six.moves import range
from six import iterkeys



class OptimizationGurobi(Optimization):
    def __init__(self):
        super(OptimizationGurobi, self).__init__()
        self.opt = Model()

    def addDecisionVars(self, pptc):
        cdef int pi
        for tc in pptc:
            for pi in range(len(pptc[tc])):
                name = self.xp(tc, pi)
                self.opt.addVar(ub=1, name=name)
        self.opt.update()

    def addBinaryVars(self, pptc, topology, types):
        g = topology.getGraph()
        cdef int pi

        for t in types:
            if t.lower() == 'node':
                for n in g.nodes_iter():
                    self.opt.addVar(vtype=GRB.BINARY, name=self.bn(n))
            elif t.lower() == 'edge':
                for u, v in g.edges_iter():
                    self.opt.addVar(vtype=GRB.BINARY, name=self.be(u, v))
            elif t.lower() == 'path':
                for tc in pptc:
                    for pi in range(len(pptc[tc])):
                        self.opt.addVar(vtype=GRB.BINARY, name=self.bp(tc, pi))
            else:
                raise FormulationException("Unknown binary variable type")

    def allocateFlow(self, pptc, allocation=None):
        cdef int pi
        for tc in pptc:
            name = self.al(tc)
            self.opt.addVar(ub=1, name=name)
        self.opt.update()
        if allocation is None:
            for tc in pptc:
                name = self.al(tc)
                lhs = LinExpr()
                for pi in range(len(pptc[tc])):
                    lhs.addTerms(1, self.opt.getVarByName(self.xp(tc, pi)))
                self.opt.addConstr(lhs == self.opt.getVarByName(name))
        else:
            for tc in pptc:
                name = self.al(tc)
                self.opt.addConstr(self.opt.getVarByName(name) == allocation,
                                   name='Allocation.tc.{}'.format(tc.ID))
        self.opt.update()

    def routeAll(self, pptc):
        for tc in pptc:
            name = self.al(tc)
            v = self.opt.getVarByName(name)
            v.lb = v.ub = 1
        self.opt.update()

    def capLinks(self, pptc, resource, linkCaps, linkCapFunc):
        cdef int pi
        expressions = defaultdict(lambda: LinExpr())
        for tc in pptc:
            for pi, path in enumerate(pptc[tc]):
                for link in path.getLinks():
                    expressions[link].addTerms(linkCapFunc(link, tc, path, resource),
                                               self.opt.getVarByName(self.xp(tc, pi)))
        for link, cap in linkCaps.iteritems():
            name = 'LinkLoad_{}_{}'.format(resource, tup2str(link))
            if self.opt.getVarByName(name) is None:
                self.opt.addVar(name=name, ub=cap)
                self.opt.update()
            self.opt.addConstr(expressions[link] == self.opt.getVarByName(name))
        self.opt.update()

    def capNodes(self, pptc, resource, nodeCaps, nodeCapFunc):
        cdef int pi
        expressions = defaultdict(lambda: LinExpr())
        for tc in pptc:
            for pi, path in enumerate(pptc[tc]):
                for node in path.getNodes():
                    expressions[node].addTerms(nodeCapFunc(node, tc, path, resource),
                                               self.opt.getVarByName(self.xp(tc, pi)))
        for node, cap in nodeCaps.iteritems():
            name = 'NodeLoad_{}_{}'.format(resource, node)
            if self.opt.getVarByName(name) is None:
                self.opt.addVar(name=name, ub=cap)
                self.opt.update()
            self.opt.addConstr(expressions[node] == self.opt.getVarByName(name))
        self.opt.update()


    def consume(self, pptc, resource, cost, nodeCaps, linkCaps):
        """
        :param pptc: paths per traffic class
        :param resource: resource to be consumed
        :param cost: cost per flow for this resource
        """
        cdef int pi
        expressions = defaultdict(lambda: LinExpr())
        for tc in pptc:
            for pi, path in enumerate(pptc[tc]):
                for node in path.getNodes():
                    expressions[node].addTerms(tc.volFlows * cost,
                                               self.opt.getVarByName(self.xp(tc, pi)))
                for link in path.getLinks():
                    expressions[link].addTerms(tc.volFlows * cost,
                                               self.opt.getVarByName(self.xp(tc, pi)))
        for node in iterkeys(nodeCaps):
            if resource not in nodeCaps[node]:
                continue
            name = 'NodeLoad_{}_{}'.format(resource, node)
            cap = nodeCaps[node][resource]
            if self.opt.getVarByName(name) is None:
                self.opt.addVar(name=name, ub=cap)
                self.opt.update()
            self.opt.addConstr(expressions[node] == self.opt.getVarByName(name))
        for link in iterkeys(linkCaps):
            if resource not in linkCaps[link]:
                continue
            name = 'LinkLoad_{}_{}'.format(resource, tup2str(link))
            cap = linkCaps[link][resource]
            if self.opt.getVarByName(name) is None:
                self.opt.addVar(name=name, ub=cap)
                self.opt.update()
            self.opt.addConstr(expressions[link] == self.opt.getVarByName(name))
        self.opt.update()

    def minLatency(self, topo, pptc, weight=1.0, norm=True):
        latency = self.opt.addVar(name="Latency", obj=weight)
        self.opt.update()
        latencyExpr = LinExpr()
        normFactor = 1.0
        if norm:
            norm = nx.diameter(topo.getGraph()) * len(pptc)
        for tc in pptc:
            for pi, path in enumerate(pptc[tc]):
                latencyExpr.addTerms(len(path) / norm, self.opt.getVarByName(self.xp(tc, pi)))
        self.opt.addConstr(latency == latencyExpr)
        self.opt.update()

    def minLinkLoad(self, resource, weight=1.0):
        objname = 'MaxLinkLoad_{}'.format(resource)
        obj = self.opt.addVar(name=objname, obj=weight)
        self.opt.update()
        prefix = 'LinkLoad_{}'.format(resource)
        for var in self.opt.getVars():
            if var.VarName.startswith(prefix):
                self.opt.addConstr(obj >= var)
        self.opt.update()

    def setTimeLimit(self, long time):
        self.opt.params.TimeLimit = time
        self.opt.update()

    def solve(self):
        # TODO: Move disabling of logging to a different place
        self.opt.setParam(GRB.param.LogToConsole, 0)
        self.opt.optimize()

    def write(self, fname):
        self.opt.write(fname + ".lp")

    def writeSolution(self, fname):
        self.write(fname + ".sol")

    def getGurobiModel(self):
        return self.opt

    def getVarValues(self):
        return {var.VarName: var.x for var in self.opt.getVars()}

    def copy(self):
        c = OptimizationGurobi()
        c.opt = self.opt.copy()
        return c

    def save(self, fname):
        pass

    def load(self, fname):
        super(OptimizationGurobi, self).load(fname)

    def getAllVariableValues(self):
        return super(OptimizationGurobi, self).getAllVariableValues()

    def addNodeCapacityConstraint(self, pptc, resource, nodecaps, nodeCapFunction):
        super(OptimizationGurobi, self).addNodeCapacityConstraint(pptc, resource, nodecaps, nodeCapFunction)

    def getSolvedObjective(self):
        return self.opt.ObjVal

    def addNodeCapacityPerPathConstraint(self, pptc, resource, nodecaps, nodeCapFunction):
        super(OptimizationGurobi, self).addNodeCapacityPerPathConstraint(pptc, resource, nodecaps, nodeCapFunction)

    def getVariableNames(self):
        super(OptimizationGurobi, self).getVariableNames()

    def addAllocateFlowConstraint(self, pptc, allocation=None):
        super(OptimizationGurobi, self).addAllocateFlowConstraint(pptc, allocation)

    def addRoutingCost(self, pptc, pathCostFunction):
        super(OptimizationGurobi, self).addRoutingCost(pptc, pathCostFunction)

    def addBudgetConstraint(self, topology, budgetFunc, bound):
        super(OptimizationGurobi, self).addBudgetConstraint(topology, budgetFunc, bound)

    def addRequireAllEdgesConstraint(self, pptc, trafficClasses=None):
        super(OptimizationGurobi, self).addRequireAllEdgesConstraint(pptc, trafficClasses)

    def setObjectiveCoeff(self, coeffs, sense):
        super(OptimizationGurobi, self).setObjectiveCoeff(coeffs, sense)

    def setPredefinedObjective(self, objective, resource=None):
        super(OptimizationGurobi, self).setPredefinedObjective(objective, resource)

    def addBinaryVariables(self, pptc, topology, types):
        super(OptimizationGurobi, self).addBinaryVariables(pptc, topology, types)

    def addMinDiffConstraint(self, prevSolution, epsilon, diffFactor):
        super(OptimizationGurobi, self).addMinDiffConstraint(prevSolution, epsilon, diffFactor)

    def addEnforceSinglePath(self, pptc, trafficClasses=None):
        super(OptimizationGurobi, self).addEnforceSinglePath(pptc, trafficClasses)

    def addRequireSomeNodesConstraint(self, pptc, trafficClasses=None, some=1):
        super(OptimizationGurobi, self).addRequireSomeNodesConstraint(pptc, trafficClasses, some)

    def addRequireAllNodesConstraint(self, pptc, trafficClasses=None):
        super(OptimizationGurobi, self).addRequireAllNodesConstraint(pptc, trafficClasses)

    def addRouteAllConstraint(self, pptc):
        super(OptimizationGurobi, self).addRouteAllConstraint(pptc)

    def addDecisionVariables(self, pptc):
        super(OptimizationGurobi, self).addDecisionVariables(pptc)

    def addPathDisableConstraint(self, pptc, trafficClasses=None):
        super(OptimizationGurobi, self).addPathDisableConstraint(pptc, trafficClasses)

    def isSolved(self):
        return self.opt.Status == GRB.OPTIMAL

    def addLinkCapacityConstraint(self, pptc, resource, linkcaps, linkCapFunction):
        super(OptimizationGurobi, self).addLinkCapacityConstraint(pptc, resource, linkcaps, linkCapFunction)

    def defineVar(self, name, coeffs, cons, lowerBound, upperBound):
        super(OptimizationGurobi, self).defineVar(name, coeffs, cons, lowerBound, upperBound)

    def getPathFractions(self, pptc, flowCarryingOnly=True):
        return super(OptimizationGurobi, self).getPathFractions(pptc, flowCarryingOnly)

    def addCapacityBudgetConstraint(self, resource, nodes, totCap):
        super(OptimizationGurobi, self).addCapacityBudgetConstraint(resource, nodes, totCap)
