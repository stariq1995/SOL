# coding=utf-8
""" The main optimization module behind SOL. Contains the high-level
generation logic, and the low-level API. Uses CPLEX under the hood"""

from __future__ import division
import copy

from sol.optimization.formulation.optbase import Optimization
from sol.utils.exceptions import InvalidConfigException, \
    FormulationException
from sol.utils.pythonHelper import tup2str, Tree, overrides
from sol.optimization.topology.traffic import PathWithMbox


try:
    # noinspection PyUnresolvedReferences
    import cplex
except ImportError as ex:
    print 'Need IBM CPLEX API, ' \
          'make sure it is installed and in your pythonpath'
    raise ex
from itertools import izip


class OptimizationCPLEX(Optimization):
    """
        A wrapper for an optimization self.cplexproblem. Uses the CPLEX solver
        under the hood.

        Consider this class to be an interface if using a different solver
        underneath.
    """

    def __init__(self):
        super(OptimizationCPLEX, self).__init__()
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
        varindex = dict(izip(v, range(len(v))))
        return varindex

    @overrides(Optimization)
    def solve(self):
        """
        Call the solver and solve the CPLEX problem
        """
        return self.cplexprob.solve()

    @overrides(Optimization)
    def defineVar(self, name, coeffs=None, const=0, lowerBound=None,
                  upperBound=None):
        self.cplexprob.variables.add(names=[name])
        if lowerBound is not None:
            self.cplexprob.variables.set_lower_bounds(name, lowerBound)
        if upperBound is not None:
            self.cplexprob.variables.set_upper_bounds(name, upperBound)
        if coeffs is None:
            return
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        var = coeffs.keys()
        mults = coeffs.values()
        var.append(varindex[name])
        mults.append(-1.0)
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair(ind=var, val=mults)],
            senses=['E'], rhs=[const])

    def defineVarSymbolic(self, name, symbolicEq):
        # TODO: support symbolic variable addition
        pass

    @overrides(Optimization)
    def setObjectiveCoeff(self, coeffs, sense):
        if sense.lower() not in ['max', 'min', 'maximize', 'minimize']:
            raise InvalidConfigException('Unknown optimization task')
        s = self.cplexprob.objective.sense.minimize
        if sense.lower() == 'max' or sense.lower() == 'maximize':
            s = self.cplexprob.objective.sense.maximize
        self.cplexprob.objective.set_sense(s)
        self.cplexprob.objective.set_linear(coeffs.items())

    @overrides(Optimization)
    def setPredefinedObjective(self, objective, resource=None, routingCostFunc=len, pptc=None):
        if objective.lower() == 'maxallflow':
            self.defineVar('TotalFlow', {name: 1 for name in
                                         self.allocationVars},
                           lowerBound=0)
            self.setObjectiveCoeff({'TotalFlow': 1}, 'max')
        elif objective.lower() == 'maxminflow':
            self.defineVar('MinFlow')
            varindex = self.getVarIndex()
            self.setObjectiveCoeff({varindex['MinFlow']: 1}, 'max')
            for allocation in self.allocationVars:
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex['MinFlow'], allocation],
                                      [1, -1])],
                    senses=['L'], rhs=[0])
        elif objective.lower() == 'minroutingcost':
            self.addRoutingCost(pptc, routingCostFunc)
            self.setObjectiveCoeff({'RoutingCost': 1}, 'min')
        elif objective.lower() == 'minmaxnodeload':
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
            self.cplexprob.objective.set_linear(varindex[maxLoadVarName], 1)
        elif objective.lower() == 'minmaxlinkload':
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
            self.cplexprob.objective.set_linear(varindex[maxLoadVarName], 1)
        else:
            raise FormulationException("Invalid objective function")

    @overrides(Optimization)
    def addDecisionVariables(self, pptc):
        var = []
        for tc in pptc:
            for pi in xrange(len(pptc[tc])):
                var.append(self.xp(tc, pi))
        self.cplexprob.variables.add(names=var, lb=[0] * len(var),
                                     ub=[1] * len(var))

    @overrides(Optimization)
    def addBinaryVariables(self, pptc, topology, types):
        graph = topology.getGraph()
        if 'node' in types:
            var = [self.bn(n) for n in graph.nodes_iter()]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var),
                ub=[1] * len(var))
        if 'edge' in types:
            var = [self.be(u, v) for u, v in graph.edges_iter()]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var), ub=[1] * len(var))
        if 'path' in types:
            var = [self.bp(k, pi) for k in pptc for pi in xrange(len(pptc[k]))]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var), ub=[1] * len(var))

    @overrides(Optimization)
    def addRoutingCost(self, pptc, routingCostFunc=len):
        coeffs = {}
        for tc in pptc:
            for pi, path in enumerate(pptc[tc]):
                coeffs[self.xp(tc, pi)] = routingCostFunc(path)
        self.defineVar('RoutingCost', coeffs, lowerBound=0)

    @overrides(Optimization)
    def addRouteAllConstraint(self, pptc):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in pptc:
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair([varindex[self.al(tc)]], [1])],
                senses=['E'], rhs=[1],
                names=['Coverage.tc.{}'.format(tc.ID)])

    @overrides(Optimization)
    def addAllocateFlowConstraint(self, pptc):
        v = self.cplexprob.variables.get_names()
        for tc in pptc:
            name = self.al(tc)
            if name not in v:
                self.cplexprob.variables.add(names=[name], lb=[0], ub=[1])
                self.allocationVars.append(name)
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in pptc:
            var = []
            for pi in range(len(pptc[tc])):
                var.append(varindex[self.xp(tc, pi)])
            mults = [1] * len(var)
            var.append(varindex[self.al(tc)])
            mults.append(-1)
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, mults)],
                senses=['E'], rhs=[0],
                names=['Allocation.tc.{}'.format(tc.ID)])

    @overrides(Optimization)
    def addNodeCapacityConstraint(self, pptc, resource, nodecaps,
                                  nodeCapFunction):
        for node in nodecaps:
            loadstr = 'Load_{}_{}'.format(resource, node)
            self.nodeLoads[node][resource][loadstr] = 1
            self.cplexprob.variables.add(names=[loadstr])

        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for node in nodecaps:
            cap = nodecaps[node]
            loadstr = 'Load_{}_{}'.format(resource, node)
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
                        mults.append(multiplier)
                        var.append(varindex[self.xp(tc, pi)])
            if cap is None:
                cv = self.nc(node, resource)
                self.cplexprob.variables.add(names=[cv], lb=[0])
                if self.bn(node) in varindex:
                    self.cplexprob.indicator_constraints.add(indvar=self.bn(node),
                                                             lin_expr=cplex.SparsePair([cv], [1]),
                                                             complemented=1,
                                                             sense="E", rhs=0)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(ind=var, val=mults),
                     cplex.SparsePair(ind=[self.nl(node, resource), cv],
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

    @overrides(Optimization)
    def addCapacityBudgetConstraint(self, resource, nodes, totCap):
        var = []
        mults = []
        varindex = self.getVarIndex()
        for node in nodes:
            var.append(varindex[self.nc(node, resource)])
            mults.append(1)
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair(var, mults)],
            senses="L", rhs=[totCap],
            names=['CapacityBudget.{}'.format(resource)]
        )

    @overrides(Optimization)
    def addLinkCapacityConstraint(self, pptc, resource, linkcaps,
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
        varindex = dict(izip(vn, range(len(vn))))
        for link in linkcaps:
            cap = linkcaps[link]
            if cap > 0:
                linkstr = tup2str(link)
                loadstr = 'LinkLoad_{}_{}'.format(resource, linkstr)
                var = [varindex[loadstr]]
                mults = [-1]
                for tc in pptc:
                    for pi, path in enumerate(pptc[tc]):
                        if link in path.getLinks():
                            multiplier = linkCapFunction(link, tc, path,
                                                         resource)
                            mults.append(multiplier)
                            var.append(varindex[self.xp(tc, pi)])
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(ind=var, val=mults),
                     cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                    senses=['E', 'L'], rhs=[0, cap],
                    names=['LinkLoad.{}.{}'.format(resource, linkstr),
                           'LinkCap.{}.{}'.format(resource, linkstr)])

    @overrides(Optimization)
    def addNodeCapacityPerPathConstraint(self, pptc, resource, nodecaps,
                                         nodeCapFunction):
        for node in nodecaps:
            loadstr = 'DLoad_{}_{}'.format(resource, node)
            self.nodeLoads[node][resource][loadstr] = 1
            self.cplexprob.variables.add(names=[loadstr])

        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
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
                        var.append(varindex[self.bp(tc, pi)])
                        mults.append(multiplier)
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults)],
                rhs=[0], senses=['E'],
                names=['DLoad.{}.{}'.format(resource, node)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair([varindex[loadstr]], [1])],
                rhs=[cap], senses=['L'],
                names=['DCap.{}.{}'.format(resource, node)])

    @overrides(Optimization)
    def addPathDisableConstraint(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi in xrange(len(pptc[tc])):
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex[self.xp(tc, pi)],
                                       varindex[self.bp(tc, pi)]],
                                      [1, -1])],
                    rhs=[0], senses='L')

    @overrides(Optimization)
    def addRequireAllNodesConstraint(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                for n in path:
                    self.cplexprob.linear_constraints.add(
                        [cplex.SparsePair([varindex[self.bp(tc, pi)],
                                           varindex[self.bn(n)]],
                                          [1, -1])],
                        rhs=[0], senses='L')

    @overrides(Optimization)
    def addRequireAllEdgesConstraint(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                for edge in path.getLinks():
                    u, v = edge
                    self.cplexprob.linear_constraints.add(
                        [cplex.SparsePair([varindex[self.bp(tc, pi)],
                                           varindex[self.be(u, v)]],
                                          [1, -1])],
                        rhs=[0], senses='L')

    @overrides(Optimization)
    def addRequireSomeNodesConstraint(self, pptc, trafficClasses=None, some=1):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                var = [varindex[self.bp(tc, pi)]]
                mults = [-1]
                for n in path:
                    var.append(varindex[self.bn(n)])
                    mults.append(1)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(var, mults)],
                    senses=['G'], rhs=[some - 1], names=['reqsomenodes.{}.{}'.format(tc.ID, pi)])

    @overrides(Optimization)
    def addBudgetConstraint(self, topology, budgetFunc, bound):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        G = topology.getGraph()
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair([varindex[self.bn(n)] for n in G.nodes_iter()],
                              [budgetFunc(n) for n in G.nodes_iter()])],
            senses=['L'], rhs=[bound],
            names=['Budget'])

    @overrides(Optimization)
    def addEnforceSinglePath(self, pptc, trafficClasses=None):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        if trafficClasses is None:
            trafficClasses = pptc.keys()
        for tc in trafficClasses:
            var = []
            for pi, path in enumerate(pptc[tc]):
                var.append(varindex[self.bp(tc, pi)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, [1] * len(var))], senses=['E'], rhs=[1],
                names=['singlepath_{}'.format(tc.ID)])

    @overrides(Optimization)
    def addMinDiffConstraint(self, prevSolution, epsilon=None, diffFactor=.5):
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
            varindex = dict(izip(v, range(len(v))))
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
                izip(names, [max(1, -epsilon + prevSolution[x])
                             for x in names]))
            self.cplexprob.variables.set_upper_bounds(
                izip(names, [min(0, epsilon + prevSolution[x])
                             for x in names]))

    @overrides(Optimization)
    def getPathFractions(self, pptc, flowCarryingOnly=True):
        result = {}
        for tc, paths in pptc.iteritems():
            result[tc] = []
            for index, path in enumerate(paths):
                newpath = copy.copy(path)
                newpath.setNumFlows(self.cplexprob.solution.get_values(
                    'x_{}_{}'.format(tc.ID, index)))
                if newpath.getNumFlows() > 0 and flowCarryingOnly:
                    result[tc].append(newpath)
                elif not flowCarryingOnly:
                    result[tc].append(newpath)
        return result

    @overrides(Optimization)
    def getSolvedObjective(self):
        return self.cplexprob.solution.get_objective_value()

    @overrides(Optimization)
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

        # def saveBasis(self):
        # self.cplexprob.start

