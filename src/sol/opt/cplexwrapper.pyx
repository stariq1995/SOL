# coding=utf-8
""" The main optimization module behind SOL. Contains the high-level
generation logic, and the low-level API. Uses CPLEX for solving the LP/ILP"""

from __future__ import division, print_function

import copy

from six.moves import zip

from sol.path import PathWithMbox
from ..utils.exceptions import InvalidConfigException
from ..utils.pythonHelper import Tree

try:
    # noinspection PyUnresolvedReferences
    import cplex
except ImportError as ex:
    print('Need IBM CPLEX API, make sure it is installed and in your PYTHONPATH')
    raise ex

from varnames import *


class OptimizationCPLEX(object):
    """
        A wrapper for an optimization self.cplexproblem. Uses the CPLEX solver
        under the hood.

        Consider this class to be an interface if using a different solver
        underneath.
    """

    def __init__(self):
        self.cplexprob = cplex.Cplex()
        self.nodeLoads = Tree()
        self.linkLoads = Tree()
        self.allocationVars = []

    def getVarIndex(self):
        """
        Get the mapping of variable names to variable indices. Helpful in dealing with
        CPLEX linear constraints.

        :return: mapping: variable->integer id
        :rtype: dict
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        return varindex

    def solve(self):
        """
        Call the solver and solve the CPLEX problem
        """
        return self.cplexprob.solve()

    def defineVar(self, name, coeffs=None, cons=0, lowerBound=None,
                  upperBound=None):
        self.cplexprob.variables.add(names=[name])
        if lowerBound is not None:
            self.cplexprob.variables.set_lower_bounds(name, lowerBound)
        if upperBound is not None:
            self.cplexprob.variables.set_upper_bounds(name, upperBound)
        if coeffs is None:
            return
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        var = coeffs.keys()
        mults = coeffs.values()
        var.append(varindex[name])
        mults.append(-1.0)
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair(ind=var, val=mults)],
            senses=['E'], rhs=[cons])

    def setObjectiveCoeff(self, coeffs, sense):
        if sense.lower() not in ['max', 'min', 'maximize', 'minimize']:
            raise InvalidConfigException('Unknown optimization task')
        s = self.cplexprob.objective.sense.minimize
        if sense.lower() == 'max' or sense.lower() == 'maximize':
            s = self.cplexprob.objective.sense.maximize
        self.cplexprob.objective.set_sense(s)
        self.cplexprob.objective.set_linear(coeffs.items())

    def maxFlow(self, pptc, weight=1.0):
        self.defineVar('TotalFlow', {al(tc): 1 for tc in pptc},
                       lowerBound=0)
        self.setObjectiveCoeff({'TotalFlow': weight}, 'max')

    def minLinkLoad(self, resource, weight=1.0):
        self.cplexprob.objective.set_sense(
            self.cplexprob.objective.sense.minimize)
        maxLoadVarName = 'LinkLoadFunction_{}'.format(resource)
        if maxLoadVarName not in \
                self.cplexprob.variables.get_names():
            self.cplexprob.variables.add(
                names=[maxLoadVarName])
        varindex = self.getVarIndex()
        for link in self.linkLoads:
            for storedRes in self.linkLoads[link]:
                if resource == storedRes:
                    for loadvar in self.linkLoads[link][storedRes]:
                        self.cplexprob.linear_constraints.add(
                            [cplex.SparsePair(
                                [varindex[maxLoadVarName],
                                 varindex[loadvar]],
                                [1.0, -1.0])],
                            senses=['G'], rhs=[0],
                            names=['MaxLinkLoad.{}.{}'.format(resource, tup2str(link))])
        self.cplexprob.objective.set_linear(varindex[maxLoadVarName], weight)

    def minLatency(self, pptc, routingCostFunc=len, weight=1.0):
        self.addRoutingCost(pptc, routingCostFunc)
        self.setObjectiveCoeff({'RoutingCost': weight}, 'min')

    # def setPredefObjective(self, objective, resource=None, routingCostFunc=len, pptc=None):
    #     if objective.lower() == MAX_MIN_FLOW:
    #         self.defineVar('MinFlow')
    #         varindex = self.getVarIndex()
    #         self.setObjectiveCoeff({varindex['MinFlow']: 1}, 'max')
    #         for allocation in self.allocationVars:
    #             self.cplexprob.linear_constraints.add(
    #                 [cplex.SparsePair([varindex['MinFlow'], allocation],
    #                                   [1, -1])],
    #                 senses=['L'], rhs=[0])

    def minNodeLoad(self, pptc, resource, weight=1.0):
        self.cplexprob.objective.set_sense(
            self.cplexprob.objective.sense.minimize)
        maxLoadVarName = 'LoadFunction_{}'.format(resource)
        if maxLoadVarName not in \
                self.cplexprob.variables.get_names():
            self.cplexprob.variables.add(
                names=[maxLoadVarName])
        varindex = self.getVarIndex()
        for node in self.nodeLoads:
            for storedRes in self.nodeLoads[node]:
                if storedRes == resource:
                    for loadvar in self.nodeLoads[node][storedRes]:
                        self.cplexprob.linear_constraints.add(
                            [cplex.SparsePair(
                                ind=[varindex[maxLoadVarName],
                                     varindex[loadvar]], val=[1.0, -1.0])],
                            senses=['G'], rhs=[0],
                            names=['MaxLoad.{}.{}'.format(resource, node)])
        self.cplexprob.objective.set_linear(varindex[maxLoadVarName], weight)

    def addDecisionVars(self, pptc):
        var = []
        for tc in pptc:
            for path in pptc[tc]:
                var.append(xp(tc, path))
        self.cplexprob.variables.add(names=var, lb=[0] * len(var),
                                     ub=[1] * len(var))

    def addBinaryVars(self, pptc, topology, types):
        graph = topology.getGraph()
        if 'node' in types:
            var = [bn(n) for n in graph.nodes_iter()]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var),
                ub=[1] * len(var))
        if 'edge' in types:
            var = [be(u, v) for u, v in graph.edges_iter()]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var), ub=[1] * len(var))
        if 'path' in types:
            var = [bp(tc, path) for tc in pptc for path in pptc[tc]]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var), ub=[1] * len(var))

    def addRoutingCost(self, pptc, routingCostFunc=len):
        coeffs = {}
        for tc in pptc:
            for path in pptc[tc]:
                coeffs[xp(tc, path)] = routingCostFunc(path)
        self.defineVar('RoutingCost', coeffs, lowerBound=0)

    def routeAll(self, pptc):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        for tc in pptc:
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair([varindex[al(tc)]], [1])],
                senses=['E'], rhs=[1],
                names=['Coverage.tc.{}'.format(tc.ID)])

    def allocateFlow(self, pptc, allocation=None):
        v = self.cplexprob.variables.get_names()
        for tc in pptc:
            name = al(tc)
            if name not in v:
                self.cplexprob.variables.add(names=[name], lb=[0], ub=[1])
                self.allocationVars.append(name)
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        if allocation is None:
            for tc in pptc:
                var = []
                mults = []
                for path in pptc[tc]:
                    var.append(varindex[xp(tc, path)])
                    mults.append(1 / tc.priority)
                mults = [1] * len(var)
                var.append(varindex[al(tc)])
                mults.append(-1)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(var, mults)],
                    senses=['E'], rhs=[0],
                    names=['Allocation.tc.{}'.format(tc.ID)])
        else:
            for tc in pptc:
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(varindex[al(tc)], [1])],
                    senses=['E'], rhs=[allocation],
                    names=['Allocation.tc.{}'.format(tc.ID)])

    def capNodes(self, pptc, resource, nodecaps,
                 nodeCapFunction):
        for node in nodecaps:
            loadstr = 'Load_{}_{}'.format(resource, node)
            self.nodeLoads[node][resource][loadstr] = 1
            self.cplexprob.variables.add(names=[loadstr])

        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        for node in nodecaps:
            cap = nodecaps[node]
            loadstr = 'Load_{}_{}'.format(resource, node)
            var = [varindex[loadstr]]
            mults = [-1]
            for tc in pptc:
                for path in pptc[tc]:
                    multiplier = 0
                    if isinstance(path, PathWithMbox):
                        if path.usesBox(node):
                            multiplier = nodeCapFunction(node, tc,
                                                         path, resource)
                    elif node in path:
                        multiplier = nodeCapFunction(node, tc, path, resource)
                    if multiplier != 0:
                        mults.append(multiplier)
                        var.append(varindex[xp(tc, path)])
            if cap is None:
                cv = nc(node, resource)
                self.cplexprob.variables.add(names=[cv], lb=[0])
                if bn(node) in varindex:
                    self.cplexprob.indicator_constraints.add(indvar=bn(node),
                                                             lin_expr=cplex.SparsePair([cv], [1]),
                                                             complemented=1,
                                                             sense="E", rhs=0)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(ind=var, val=mults),
                     cplex.SparsePair(ind=[nl(node, resource), cv],
                                      val=[1, -1])],
                    senses="EL", rhs=[0, 0],
                    names=['Load.{}.{}'.format(resource, node),
                           'Cap.{}.{}'.format(resource, node)])
            else:
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(ind=var, val=mults),
                     cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                    senses=['E', 'L'], rhs=[0, cap],
                    names=['Load.{}.{}'.format(resource, node),
                           'Cap.{}.{}'.format(resource, node)])

    def nodeBudget(self, resource, nodes, totCap):
        var = []
        mults = []
        varindex = self.getVarIndex()
        for node in nodes:
            var.append(varindex[nc(node, resource)])
            mults.append(1)
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair(var, mults)],
            senses="L", rhs=[totCap],
            names=['CapacityBudget.{}'.format(resource)])

    def capLinks(self, pptc, resource, linkcaps,
                 linkCapFunction):
        for link in linkcaps:
            u, v = link
            cap = linkcaps[link]
            if cap > 0:
                linkstr = tup2str((u, v))
                loadstr = 'LinkLoad_{}_{}'.format(resource, linkstr)
                self.linkLoads[link][resource][loadstr] = 1
                self.cplexprob.variables.add(names=[loadstr])

        vn = self.cplexprob.variables.get_names()
        varindex = dict(zip(vn, range(len(vn))))
        for link in linkcaps:
            cap = linkcaps[link]
            if cap > 0:
                linkstr = tup2str(link)
                loadstr = 'LinkLoad_{}_{}'.format(resource, linkstr)
                var = [varindex[loadstr]]
                mults = [-1]
                for tc in pptc:
                    for path in pptc[tc]:
                        if link in path.getLinks():
                            multiplier = linkCapFunction(link, tc, path,
                                                         resource)
                            mults.append(multiplier)
                            var.append(varindex[xp(tc, path)])
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(ind=var, val=mults),
                     cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                    senses=['E', 'L'], rhs=[0, cap],
                    names=['LinkLoad.{}.{}'.format(resource, linkstr),
                           'LinkCap.{}.{}'.format(resource, linkstr)])

    def capNodesPathResource(self, pptc, resource, nodecaps,
                             nodeCapFunction):
        for node in nodecaps:
            loadstr = 'DLoad_{}_{}'.format(resource, node)
            self.nodeLoads[node][resource][loadstr] = 1
            self.cplexprob.variables.add(names=[loadstr])

        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        for node in nodecaps:
            cap = nodecaps[node]
            loadstr = 'DLoad_{}_{}'.format(resource, node)
            var = [varindex[loadstr]]
            mults = [-1]
            for tc in pptc:
                for pi, path in enumerate(pptc[tc]):
                    multiplier = 0
                    if isinstance(path, PathWithMbox):
                        if path.usesBox(node):
                            multiplier = nodeCapFunction(node, tc,
                                                         path, resource)
                    elif node in path:
                        multiplier = nodeCapFunction(node, tc, path, resource)
                    if multiplier != 0:
                        var.append(varindex[bp(tc, path)])
                        mults.append(multiplier)
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults)],
                rhs=[0], senses=['E'],
                names=['DLoad.{}.{}'.format(resource, node)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair([varindex[loadstr]], [1])],
                rhs=[cap], senses=['L'],
                names=['DCap.{}.{}'.format(resource, node)])

    def addPathDisableConstraint(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for path in pptc[tc]:
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex[xp(tc, path)],
                                       varindex[bp(tc, path)]],
                                      [1, -1])],
                    rhs=[0], senses='L')

    def reqAllNodes(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                for n in path:
                    self.cplexprob.linear_constraints.add(
                        [cplex.SparsePair([varindex[bp(tc, path)],
                                           varindex[bn(n)]],
                                          [1, -1])],
                        rhs=[0], senses='L')

    def reqAllEdges(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                for edge in path.getLinks():
                    u, v = edge
                    self.cplexprob.linear_constraints.add(
                        [cplex.SparsePair([varindex[bp(tc, path)],
                                           varindex[be(u, v)]],
                                          [1, -1])],
                        rhs=[0], senses='L')
    reqAllLinks = reqAllEdges  # method alias

    def reqSomeNodes(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                var = [varindex[bp(tc, path)]]
                mults = [-1]
                for n in path:
                    var.append(varindex[bn(n)])
                    mults.append(1)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(var, mults)],
                    senses=['G'], rhs=[0], names=['reqsomenodes.{}.{}'.format(tc.ID, pi)])

    def addNodeBudget(self, topology, budgetFunc, bound):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        G = topology.getGraph()
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair([varindex[bn(n)] for n in G.nodes_iter()],
                              [budgetFunc(n) for n in G.nodes_iter()])],
            senses=['L'], rhs=[bound],
            names=['Budget'])

    def forceSinglePath(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(zip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            var = []
            for pi, path in enumerate(pptc[tc]):
                var.append(varindex[bp(tc, path)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, [1] * len(var))], senses=['E'], rhs=[1],
                names=['singlepath_{}'.format(tc.ID)])

    def minDiffConstraint(self, prevSolution, epsilon=None, diffFactor=.5):
        names = [x for x in prevSolution if x.startswith('x')]
        if epsilon is None:
            epsdict = {}
            for x in names:
                _, a, b = x.split('_')
                # print a, b
                ep = 'd_{}_{}'.format(a, b)
                epsdict[x] = ep
            self.cplexprob.variables.add(names=epsdict.values(),
                                         lb=[0] * (len(epsdict)),
                                         ub=[1] * (len(epsdict)))
            self.cplexprob.variables.add(names=['maxdiff'], lb=[0], ub=[1])
            v = self.cplexprob.variables.get_names()
            # print v
            varindex = dict(zip(v, range(len(v))))
            for x in names:
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex[x], varindex[epsdict[x]]],
                                      [1, -1])],
                    rhs=[prevSolution[x]], senses='L')
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex[x], varindex[epsdict[x]]],
                                      [1, 1])],
                    rhs=[prevSolution[x]], senses='G')
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(
                        [varindex['maxdiff'], varindex[epsdict[x]]],
                        [1, -1])],
                    rhs=[0], senses='G')

            self.cplexprob.objective.set_linear(
                [(i, q * (1 - diffFactor)) for i, q in
                 enumerate(self.cplexprob.objective.get_linear())])
            self.cplexprob.objective.set_linear(
                varindex['maxdiff'],
                diffFactor if self.cplexprob.objective.get_sense()
                              == self.cplexprob.objective.sense.minimize
                else -diffFactor)
        else:
            self.cplexprob.variables.set_lower_bounds(
                zip(names, [max(1, -epsilon + prevSolution[x])
                            for x in names]))
            self.cplexprob.variables.set_upper_bounds(
                zip(names, [min(0, epsilon + prevSolution[x])
                            for x in names]))

    def getPathFractions(self, pptc, flowCarryingOnly=True):
        result = {}
        for tc, paths in pptc.iteritems():
            result[tc] = []
            for path in paths:
                newpath = copy.copy(path)
                newpath.setFlowFraction(self.cplexprob.solution.get_values(
                    xp(tc, path)))
                if newpath.getFlowFraction() > 0 and flowCarryingOnly:
                    result[tc].append(newpath)
                elif not flowCarryingOnly:
                    result[tc].append(newpath)
        return result

    def getSolvedObjective(self):
        return self.cplexprob.solution.get_objective_value()

    def getAllVariableValues(self):
        return dict(zip(self.cplexprob.variables.get_names(),
                        self.cplexprob.solution.get_values()))

    def write(self, fname):
        """
        Write the LP formulation to disk

        :param fname: the output file name
        """
        self.cplexprob.write(fname, 'lp')

    def writeSolution(self, fname):
        """
        Write the LP solution to disk

        :param fname: the output filename
        """
        self.cplexprob.write(fname, 'sol')

    def setName(self, newName):
        """
        Set the name of the current optimization problem.

        :param newName: the new name for this problem
        :type: str
        """
        self.cplexprob.set_problem_name(newName)

    def setSolveTimeLimit(self, time):
        """
        Set a time limit on execution time

        :param time: timeout in seconds, after which to give up solving
        """
        self.cplexprob.parameters.timelimit.set(time)

    def getCPLEXObject(self):
        """
        :return: the underlying CPLEX problem instance

        .. warning::
            This is really low-level, know what you're doing!
        """
        return self.cplexprob

    def getVariableNames(self):
        return self.cplexprob.variables.get_names()

    def isSolved(self):
        return self.cplexprob.solution.status in [cplex.Cplex.solution.status.optimal,
                                                  cplex.Cplex.solution.status.optimal_tolerance,
                                                  cplex.Cplex.solution.status.MIP_optimal]

    def save(self, fname):
        #TODO: add support for ILP/MIP starts
        return self.cplexprob.solution.basis.write(fname)

    def load(self, fname):
        return self.cplexprob.start.read_basis(fname)
