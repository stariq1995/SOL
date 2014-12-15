# coding=utf-8
""" The main optimization module behind SOL. Contains the high-level
generation logic, and the low-level API. Uses CPLEX under the hood"""

from __future__ import division
import copy

from sol.optimization.formulation.optbase import Optimization
from sol.util.exceptions import InvalidConfigException, \
    FormulationException
from sol.util.pythonHelper import tup2str, Tree
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

    def solve(self):
        """
        Call the solver and solve the CPLEX problem
        """
        return self.cplexprob.solve()

    def getCPLEXObject(self):
        """
        :return: the underlying CPLEX problem instance

        .. note::
            This is really low-level, know what you're doing!
        """
        return self.cplexprob

    def defineVar(self, name, coeffs=None, const=0, lowerBound=None,
                  upperBound=None):
        """ Utility function to define an (almost) arbitrary variable.

        :param name: name of the variable
        :param coeffs: coefficients of other variables that define this
            variable, a dictionary of strings to floats.
            If None, then only the name is defined, with no value assigned
            to it.
        :param const: any non-coefficient slack
        :param lowerBound: lower bound on the variable
        :param upperBound: upper bound on the variable
        """
        self.cplexprob.variables.add(names=[name])
        if lowerBound is not None:
            self.cplexprob.variables.set_lower_bounds((name, lowerBound))
        if upperBound is not None:
            self.cplexprob.variables.set_upper_bounds((name, upperBound))
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

    def setObjectiveCoeff(self, coeffs, sense):
        """
        Set the objective coefficients for given variables

        :param coeffs: dictionary mapping variables to coefficients
        :param sense: *min* or *max* indicates whether we are minimizing or
            maximizing the objective
        """
        if sense.lower() not in ['max', 'min', 'maximize', 'minimize']:
            raise InvalidConfigException('Unknown optimization task')
        s = self.cplexprob.objective.sense.minimize
        if sense.lower() == 'max' or sense.lower() == 'maximize':
            s = self.cplexprob.objective.sense.maximize
        self.cplexprob.objective.set_sense(s)
        self.cplexprob.objective.set_linear(coeffs.items())

    def setPredefinedObjective(self, objective, resource):
        """
        Set a predefined objective. See :ref:`definedObjectives` for the list
            of supported objectives
        .. note:
            All variables must be defined before calling this function

        :param objective: predefined objective name
        :param resource: some objectives (such as minmaxnodeload) come with a
            resource parameter. Set it here.
        :raise FormulationException: if passed objective is not supported
        """
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
                    senses=['G'], rhs=[0])
        elif objective.lower() == 'minroutingcost':
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

    def addDecisionVariables(self, pptc):
        """ Add and set bounds on the flow fraction variables

        :param pptc: paths per commodity
        """
        var = []
        for tc in pptc:
            for pi in xrange(len(pptc[tc])):
                var.append(self.xp(tc, pi))
        self.cplexprob.variables.add(names=var, lb=[0] * len(var),
                                     ub=[1] * len(var))

    def addBinaryVariables(self, pptc, topology, types):
        """
        Add binary variables to this formulation

        :param pptc: paths per traffic class
        :param topology: the topology we are operating on
        :param types: types of binary variables to add. Allowed values are
            'node', 'edge', and 'path'
        """
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

    def addRoutingCost(self, pptc):
        """ Defines the routing cost constraint

        :param pptc: paths per traffic class
        """
        coeffs = {}
        for tc in pptc:
            for pi, path in enumerate(pptc[tc]):
                coeffs[self.xp(tc, pi)] = len(path)
        self.defineVar(self.cplexprob, 'RoutingCost', coeffs)

    def addRouteAllConstraint(self, pptc):
        """ Adds the constraint to ensure all traffic is routed

        :param pptc: paths per traffic class
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in pptc:
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair([varindex[self.al(tc)]], [1])],
                senses=['E'], rhs=[1],
                names=['Coverage.tc.{}'.format(tc.ID)])

    def addAllocateFlowConstraint(self, pptc):
        """
        Allocate flow for each traffic class

        :param pptc: paths per traffic class
        """
        v = self.cplexprob.variables.get_names()
        for tc in pptc:
            name = self.al(tc)
            if self.al(tc) not in v:
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

            # def addDemandConstraints(self, pptc, tclasses=None,
            # allocationval=None, setEqual=False):
            # """ Adds demand constraints for given traffic classes
            #
            #     :param pptc: paths per traffic class
            #     :param tclasses: traffic classes for which the allocation constraints
            #         should be added. If None, all traffic classes from *pptc* will be
            #         used
            #     :param allocationval: exisiting allocation values for the traffic
            #         classes.
            #         If none, appropriate decision variables will be created
            #     :param setEqual: If True, ensure that allocation values for given
            #         traffic classes are equal to each other
            #     """
            # v = self.cplexprob.variables.get_names()
            # for tc in tclasses:
            #     if 'allocation' not in v:
            #         self.cplexprob.variables.add(
            #             names=['allocation_{}'.format(tc.ID)],
            #             lb=[0], ub=[tc.volume])
            # v = self.cplexprob.variables.get_names()
            # varindex = dict(izip(v, range(len(v))))
            # if tclasses is None:
            #     tclasses = pptc.iterkeys()
            # for tc in tclasses:
            #     var = []
            #     mults = []
            #     for pi in range(len(pptc[tc])):
            #         var.append(varindex[self._xp(tc, pi)])
            #         mults.append(tc.volume)
            #     self.cplexprob.linear_constraints.add(
            #         [cplex.SparsePair(var, mults)],
            #         senses=['L'], rhs=[1],
            #         names=['DemandCap.tc.{}'.format(tc.ID)])
            #     mults = [x / tc.weight for x in mults]
            #     if allocationval is None:
            #         var.append(varindex['allocation_{}'.format(tc.ID)])
            #         mults.append(-1)
            #         rhs = [0]
            #     else:
            #         rhs = [-allocationval]
            #     self.cplexprob.linear_constraints.add(
            #         [cplex.SparsePair(var, mults)],
            #         senses='G', rhs=rhs,
            #         names=['Demand.tc.{}'.format(tc.ID)])
            # if setEqual:
            #     for k1, k2 in itertools.izip(tclasses, tclasses[1:]):
            #         self.cplexprob.linear_constraints.add(
            #             [cplex.SparsePair([varindex['allocation_{}'.format(k1.ID)],
            #                                varindex['allocation_{}'.format(k2.ID)]],
            #                               [1, -1])],
            #             rhs=[0], senses='E')

    def addNodeCapacityConstraint(self, pptc, resource, nodecaps,
                                   nodeCapFunction):
        """
        Add node capacity constraints

        :param pptc: paths per commodity
        :param resource: the resource for which we are adding the capacity
            constraints
        :param nodecaps: dictionary containing a mapping of nodes to
        to capacities for this particular resource. For exapmle::
                nodecaps[1] = 10
                nodecaps[3] = 4

            means that capacity of node 1 is 10 units,
            capacity of node 3 is 4 units
        :param nodeCapFunction: user defined function
        """

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
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults),
                 cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                senses=['E', 'L'], rhs=[0, cap],
                names=['Load.{}.{}'.format(resource, node),
                       'Cap.{}.{}'.format(resource, node)])

    def addLinkCapacityConstraint(self, pptc, resource, linkcaps,
                           linkCapFunction):
        """
        Add node capacity constraints

        :param pptc: paths per commodity
        :param resource: the resource for which we are adding the capacity
            constraints
        :param linkcaps: dictionary containing a mapping of links to
        to capacities for this particular resource. For exapmle::
                linkcaps[(1,3)] = 10

            means that link capacity between nodes 1 and 3 is 10 units.
        :param linkCapFunction: user defined function
        """
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

    def addNodeCapacityIfActive(self, pptc, resource, nodecaps,
                                nodeCapFunction):
        """
        :param pptc:
        :param resource:
        :param nodecaps:
        :param nodeCapFunction
        :return:
        """
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

    def addPathDisableConstraint(self, pptc, trafficClasses):
        """
        Add *enforcePathDisable* constraint. That is only allow traffic flow if
        binary path variable is enabled.

        :param pptc: paths per traffic class
        :param trafficClasses: traffic classes for which this constraint
            should take effect
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in trafficClasses:
            for pi in xrange(len(pptc[tc])):
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex[self.xp(tc, pi)],
                                       varindex[self.bp(tc, pi)]],
                                      [1, -1])],
                    rhs=[0], senses='L', names=['pathdisable'])

    def addRequireAllNodesConstraint(self, pptc, trafficClasses):
        """

        :param pptc:
        :param trafficClasses:
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                for n in path:
                    self.cplexprob.linear_constraints.add(
                        [cplex.SparsePair([varindex[self.bp(tc, pi)],
                                           varindex[self.bn(n)]],
                                          [1, -1])],
                        rhs=[0], senses='L', names='reqallnodes')

    def addRequireAllEdgesConstraint(self, pptc, trafficClasses):
        """

        :param pptc:
        :param trafficClasses:
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                for edge in path.getLinks():
                    u, v = edge
                    self.cplexprob.linear_constraints.add(
                        [cplex.SparsePair([varindex[self.bp(tc, pi)],
                                           varindex[self.be(u, v)]],
                                          [1, -1])],
                        rhs=[0], senses='L', names=['reqalledges'])

    def addRequireSomeNodesConstraint(self, pptc, trafficClasses):
        """

        :param pptc:
        :param trafficClasses
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                var = [varindex[self.bp(tc, pi)]]
                mults = [-1]
                for n in path:
                    var.append(varindex[self.bn(n)])
                    mults.append(1)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(var, mults)],
                    senses=['G'], rhs=[0], names=['reqallnodes'])

    def addBudgetConstraint(self, topology, budgetFunc, bound):
        """

        :type topology: :py:class:`~sol.optimization.topology.Topology`
        :param topology:
        :param budgetFunc:
        :param bound:
        """

        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        G = topology.getGraph()
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair([varindex[self.bn(n)] for n in G.nodes_iter()],
                              [budgetFunc(n) for n in G.nodes_iter()])],
            senses=['L'], rhs=[bound],
            names=['Budget'])

    def addEnforceSinglePath(self, pptc):
        """

        :param self.cplexprob:
        :param pptc:
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in pptc:
            var = []
            for pi, path in enumerate(pptc[tc]):
                var.append(varindex[self.bp(tc, pi)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, [1] * len(var))], senses=['E'], rhs=[1],
                names=['singlepath_{}'.format(tc.ID)])

    # def addPowerConstraint(self, nodeConsumption, edgeConsumption,
    # normalize=True):
    # """
    #
    # :param self.cplexprob:
    # :param nodeConsumption:
    # :param edgeConsumption:
    # :param normalize:
    # """
    # self.cplexprob.variables.add(names=['linkpower', 'switchpower'],
    # lb=[0, 0])
    # v = self.cplexprob.variables.get_names()
    # varindex = dict(izip(v, range(len(v))))
    # norm = sum(nodeConsumption.values()) + sum(edgeConsumption.values()) \
    # if normalize else 1
    # self.cplexprob.linear_constraints.add([cplex.SparsePair(
    # [varindex['binedge_{}_{}'.format(a, b)] for (a, b) in
    #          edgeConsumption] +
    #         [varindex['linkpower']],
    #         [edgeConsumption[link] / norm for link in edgeConsumption] + [-1])],
    #                                           rhs=[0], senses=['E'])
    #     self.cplexprob.linear_constraints.add([cplex.SparsePair(
    #         [varindex['binnode_{}'.format(u)] for u in nodeConsumption] +
    #         [varindex['switchpower']],
    #         [nodeConsumption[node] / norm for node in nodeConsumption] + [-1])],
    #                                           rhs=[0], senses=['E'])

    def addMinDiffConstraint(self, prevSolution, epsilon=None, diffFactor=.5):
        #TODO: check this method
        """

        :param self.cplexprob:
        :param prevSolution:
        :param epsilon:
        :param diffFactor:
        """
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


            # def addFailedSwitchConstraints(prob, ppk, failedSwitches):
            #
            #     """
            #
            #     :param self.cplexprob:
            #     :param ppk:
            #     :param failedSwitches:
            #     """
            #
            #     v = self.cplexprob.variables.get_names()
            #     varindex = dict(izip(v, range(len(v))))
            #     for k in ppk:
            #         for ind, path in enumerate(ppk[k]):
            #             for failedNode in failedSwitches:
            #                 if failedNode in path:
            #                     self.cplexprob.linear_constraints.add(
            #                         [cplex.SparsePair([varindex[_xp(k, ind)]], [1])],
            #                         rhs=[0], senses='E')


    def getPathFractions(self, pptc, flowCarryingOnly=True):
        """
        Gets flow fractions per each path from the solution

        :param pptc: paths per traffic class
        :param flowCarryingOnly: only return flow-carrying paths (with non-zero fractions)
        :rtype: dict
        :returns: dictionary of paths to fractions
        """
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

    def write(self, fname):
        self.cplexprob.write(fname, 'lp')

    def writeSolutions(self, fname):
        self.cplexprob.write(fname, 'sol')

    def getSolvedObjective(self):
        return self.cplexprob.solution.get_objective_value()

    def setName(self, newName):
        """
        Set the name of the current optimization problem.

        :param newName:
        """
        self.cplexprob.set_problem_name(newName)

    def getAllVariableValues(self):
        raise NotImplementedError()

    def setSolveTimeLimit(self, time):
        # TODO: implement time limit
        pass
