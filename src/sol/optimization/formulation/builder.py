# coding=utf-8
""" The main optimization module behind SOL. Contains the high-level
generation logic, and the low-level API. Uses CPLEX under the hood"""

from __future__ import division
from collections import defaultdict
import itertools

from sol.util.exceptions import InvalidConfigException, \
    NoPathsException, FormulationException
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


class Optimization(object):
    """
        A wrapper for an optimization self.cplexproblem. Uses the CPLEX solver
        under the hood.

        Consider this class to be an interface if using a different solver
        underneath.
    """

    # TODO: add allowed objectives
    """
        Predefined objectives that can be used for optimization
    """
    definedObjectives = []

    def __init__(self):
        """
        Create a new optimization problem instance
        """
        self.cplexprob = cplex.Cplex()
        self.nodeLoads = defaultdict(lambda x: [])
        self.linkLoads = defaultdict(lambda x: [])

    @staticmethod
    def _xp(trafficClass, pathIndex):
        """ Convenience method for formatting a decision variable

        :param trafficClass: the commodity objects, needed for the ID
        :param pathIndex: index of the path
        :returns: variable name of the form *x_classid_pathindex*
        :rtype: str
        """
        return 'x_{}_{}'.format(trafficClass.ID, pathIndex)

    @staticmethod
    def _bn(node):
        return 'binnode_{}'.format(node)

    @staticmethod
    def _be(head, tail):
        return 'binedge_{}_{}'.format(head, tail)

    @staticmethod
    def _bp(trafficClass, pathIndex):
        return 'binpath_{}_{}'.format(trafficClass.ID, pathIndex)

    def _getVarIndex(self):
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        return varindex

    def solve(self):
        """
        Call the solver and solve the self.cplexproblem
        """
        return self.cplexprob.solve()

    def getCPLEXObject(self):
        """
        :return: the underlying CPLEX self.cplexproblem instance

        ..note::
            This is really low-level, know what you're doing!
        """
        return self.cplexprob

    # TODO: implement a better setObjective and defineVar
    def defineVar(self, name, coeffs, const=0):
        """ Utility function to define an (almost) arbitrary variable.

        :param name: name of the variable
        :param coeffs: coefficients of other variables that define this
            variable, a dictionary of strings to floats.
            If None, then only the name is defined, with no value or no bounds
            assigned to it.
        :param const: any non-coefficient slack
        """
        self.cplexprob.variables.add(names=[name])
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

    def setObjective(self, coeffs, sense):
        """
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

    def setPredefinedObjective(self, objective, resource=None):
        """

        :param objective: predefined objective name
        :param resource:
        :raise FormulationException: if passed objective is not predefined
        """
        # TODO: finish the rest of the objectives
        if objective == 'maxallflow':
            pass
        elif objective.lower() == 'minmaxnodeload':
            self.cplexprob.objective.set_sense(
                self.cplexprob.objective.sense.minimize)
            if 'LoadFunction_{}'.format(resource) not in \
                    self.cplexprob.variables.get_names():
                self.cplexprob.variables.add(
                    names=['LoadFunction_{}'.format(resource)])
            varindex = self._getVarIndex()
            for loadvar in self.nodeLoads[resource]:
                node = loadvar.split('_')[-1]
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(
                        ind=[varindex['LoadFunction_{}'.format(resource)],
                             varindex[loadvar]], val=[1.0, -1.0])],
                    senses=['G'], rhs=[0],
                    names=['MaxLoad.{}.{}'.format(resource, node)])
            objective.cplex.set_linear((varindex['LoadFunction_{}'.format(
                resource)], 1))
        elif objective.lower() == 'minmaxlinkload':
            self.cplexprob.objective.set_sense(
                self.cplexprob.objective.sense.minimize)
            if 'LinkLoadFunction_{}'.format(resource) not in \
                    self.cplexprob.variables.get_names():
                self.cplexprob.variables.add(
                    names=['LinkLoadFunction_{}'.format(resource)])
            varindex = self._getVarIndex()
            for loadvar in self.linkLoads[resource]:
                link = loadvar.split('_')[-2:]
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(
                        [varindex['LinkLoadFunction_{}'.format(resource)],
                         varindex[loadvar]],
                        [1.0, -1.0])],
                    senses=['G'], rhs=[0],
                    names=['MaxLinkLoad.{}.{}'.format(resource, tup2str(link))])
            objective.cplex.set_linear((varindex['LinkLoadFunction_{}'.format(
                resource)], 1))
        else:
            raise FormulationException("Invalid objective function")

    def addDecisionVariables(self, pptc):
        """ Add and set bounds on the flow fraction variables

        :param pptc: paths per commodity
        """
        var = []
        for tc in pptc:
            for pi in xrange(len(pptc[tc])):
                var.append(self._xp(tc, pi))
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
            var = [self._bn(n) for n in graph.nodes_iter()]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var),
                ub=[1] * len(var))
        if 'edge' in types:
            var = [self._be(u, v) for u, v in graph.edges_iter()]
            self.cplexprob.variables.add(
                names=var,
                types=[self.cplexprob.variables.type.binary] * len(var),
                lb=[0] * len(var), ub=[1] * len(var))
        if 'path' in types:
            var = [self._bp(k, pi) for k in pptc for pi in xrange(len(pptc[k]))]
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
                coeffs[self._xp(tc, pi)] = len(path)
        self.defineVar(self.cplexprob, 'RoutingCost', coeffs)

    def addRouteAllConstraints(self, pptc):
        """ Adds the constraint to ensure all traffic is routed

        :param pptc: paths per traffic class
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in pptc:
            var = []
            for pi in range(len(pptc[tc])):
                var.append(varindex[self._xp(tc, pi)])
            mults = [1] * len(var)
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, mults)],
                senses=['E'], rhs=[1],
                names=['Coverage.tc.{}'.format(tc.ID)])

    def addAllocateFlowConstraints(self, pptc, tclasses=None,
                                   allocationval=None, setEqual=False):
        # XXX:FIX THIS METHOD
        """ Adds demand constraints for given traffic classes

        :param pptc: paths per traffic class
        :param tclasses: traffic classes for which the allocation constraints
            should be added. If none, all traffic classes from *pptc* will be
            used
        :param allocationval: exisiting allocation values for the traffic
            classes.
            If none, appropriate decision variables will be created
        :param setEqual: If True, ensure that allocation values for given
            traffic classes are equal to each other
        """
        v = self.cplexprob.variables.get_names()
        for tc in tclasses:
            if 'allocation' not in v:
                self.cplexprob.variables.add(
                    names=['allocation_{}'.format(tc.ID)],
                    lb=[0], ub=[tc.volume])
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        if tclasses is None:
            tclasses = pptc.iterkeys()
        for tc in tclasses:
            var = []
            mults = []
            for pi in range(len(pptc[tc])):
                var.append(varindex[self._xp(tc, pi)])
                mults.append(tc.volume)
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, mults)],
                senses=['L'], rhs=[tc.volume],
                names=['DemandCap.tc.{}'.format(tc.ID)])
            mults = [x / tc.weight for x in mults]
            if allocationval is None:
                var.append(varindex['allocation_{}'.format(tc.ID)])
                mults.append(-1)
                rhs = [0]
            else:
                rhs = [-allocationval]
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(var, mults)],
                senses='G', rhs=rhs,
                names=['Demand.tc.{}'.format(tc.ID)])
        if setEqual:
            for k1, k2 in itertools.izip(tclasses, tclasses[1:]):
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair([varindex['allocation_{}'.format(k1.ID)],
                                       varindex['allocation_{}'.format(k2.ID)]],
                                      [1, -1])],
                    rhs=[0], senses='E')

    def addNodeCapacityConstraints(self, pptc, resource, nodecaps,
                                   nodeCapFunction):
        """
        Add node capacity constraints

        :param pptc: paths per commodity
        :param resource: the resource for which we are adding the capacity
            constraints
        :param nodecaps: dictionary containing a mapping of nodes to
        to capacities for this particular resource. For exapmle::
                nodecap[1] = 10
                nodecap[3] = 4

            means that cpu capacity of node 1 is 10 units,
            memory capacity of node 3 is 4 units
        :param nodeCapFunction: user defined function
        """

        for node in nodecaps:
            loadstr = 'Load_{}_{}'.format(resource, node)
            self.nodeLoads['resource'].append(loadstr)
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
                        var.append(varindex[self._xp(tc, pi)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults),
                 cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                senses=['E', 'L'], rhs=[0, cap],
                names=['Load.{}.{}'.format(resource, node),
                       'Cap.{}.{}'.format(resource, node)])

    def addLinkConstraints(self, pptc, resource, linkcaps,
                           linkCapFunction):
        # TODO: document
        """
        :param pptc: paths per commodity
        :param resource:
        :param linkcaps: dictionary mapping links to capacities
        :param linkCapFunction:
        """
        for link in linkcaps:
            u, v = link
            cap = linkcaps[link]
            if cap > 0:
                linkstr = tup2str((u, v))
                loadstr = 'LinkLoad_{}_{}'.format(resource, linkstr)
                self.linkLoads[resource].append(loadstr)
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
                            var.append(varindex[self._xp(tc, pi)])
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(ind=var, val=mults),
                     cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                    senses=['E', 'L'], rhs=[0, cap],
                    names=['LinkLoad.{}.{}'.format(resource, linkstr),
                           'LinkCap.{}.{}'.format(resource, linkstr)])

    def addDiscreteLoadConstraints(self, pptc, resource, nodecaps,
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
                    if isinstance(path, PathWithMbox):
                        if path.usesBox(node):
                            multiplier = nodeCapFunction(node, tc,
                                                         path, resource)
                    elif node in path:
                        multiplier = nodeCapFunction(node, tc, path, resource)
                    if multiplier != 0:
                        var.append(varindex[self._bp(tc, pi)])
                        mults.append(multiplier)
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults)],
                rhs=[0], senses=['E'],
                names=['DLoad.{}.{}'.format(resource, node)])
            self.cplexprob.linear_constraints.add(
                [cplex.SparsePair([varindex[loadstr]], [1])],
                rhs=[cap], senses=['L'],
                names=['DCap.{}.{}'.format(resource, node)])

    def addPathDisable(self, pptc, trafficClasses):
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
                    [cplex.SparsePair([varindex[self._xp(tc, pi)],
                                       varindex[self._bp(tc, pi)]],
                                      [1, -1])],
                    rhs=[0], senses='L', names=['pathdisable'])

    def addRequireAllNodesConstraints(self, pptc, trafficClasses):
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
                        [cplex.SparsePair([varindex[self._bp(tc, pi)],
                                           varindex[self._bn(n)]],
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
                        [cplex.SparsePair([varindex[self._bp(tc, pi)],
                                           varindex[self._be(u, v)]],
                                          [1, -1])],
                        rhs=[0], senses='L', names=['reqalledges'])

    def addRequireSomeNodesConstraints(self, pptc, trafficClasses):
        """

        :param pptc:
        :param trafficClasses
        """
        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        for tc in trafficClasses:
            for pi, path in enumerate(pptc[tc]):
                var = [varindex[self._bp(tc, pi)]]
                mults = [-1]
                for n in path:
                    var.append(varindex[self._bn(n)])
                    mults.append(1)
                self.cplexprob.linear_constraints.add(
                    [cplex.SparsePair(var, mults)],
                    senses=['G'], rhs=[0], names=['reqallnodes'])

    def addBudgetConstraint(self, topology, func, bound):
        """

        :type topology: :py:class:`~sol.optimization.topology.Topology`
        :param topology:
        :param func:
        :param bound:
        """

        v = self.cplexprob.variables.get_names()
        varindex = dict(izip(v, range(len(v))))
        G = topology.getGraph()
        self.cplexprob.linear_constraints.add(
            [cplex.SparsePair([varindex[self._bn(n)] for n in G.nodes_iter()],
                              [func(n) for n in G.nodes_iter()])],
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
                var.append(varindex[self._bp(tc, pi)])
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
    #     v = self.cplexprob.variables.get_names()
    #     varindex = dict(izip(v, range(len(v))))
    #     norm = sum(nodeConsumption.values()) + sum(edgeConsumption.values()) \
    #         if normalize else 1
    #     self.cplexprob.linear_constraints.add([cplex.SparsePair(
    #         [varindex['binedge_{}_{}'.format(a, b)] for (a, b) in
    #          edgeConsumption] +
    #         [varindex['linkpower']],
    #         [edgeConsumption[link] / norm for link in edgeConsumption] + [-1])],
    #                                           rhs=[0], senses=['E'])
    #     self.cplexprob.linear_constraints.add([cplex.SparsePair(
    #         [varindex['binnode_{}'.format(u)] for u in nodeConsumption] +
    #         [varindex['switchpower']],
    #         [nodeConsumption[node] / norm for node in nodeConsumption] + [-1])],
    #                                           rhs=[0], senses=['E'])

    def addMinDiffConstraints(self, prevSolution, epsilon=None, diffFactor=.5):
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
            self.cplexprob.objective.set_linear(varindex['maxdiff'],
                                                diffFactor if self.cplexprob.objective.get_sense() == self.cplexprob.objective.sense.minimize else -diffFactor)
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


def generateFormulation(topology, ppk, resources=None, discreteResources=None,
                        objective=None, task=None,
                        constraints=None, budgetBound=None, budgetFunc=None,
                        allocationvals=None, saturatedcomm=None,
                        unsaturatedcomm=None, mipgap=None, timelimit=None,
                        diffFactor=0, **kwargs):
    """Generate the formulation based on the high-level configuration

    :param resources:
    :param discreteResources:
    :param objective:
    :param task:
    :param constraints:
    :param budgetBound:
    :param budgetFunc:
    :param allocationvals:
    :param saturatedcomm:
    :param unsaturatedcomm:
    :param mipgap:
    :param timelimit:
    :param topology: the topology on which we are running
    :param ppk: paths per commodity
    :param kwargs: all other keyword arguments
    """

    # Do a quick sanity check
    # if task.lower() not in ['max', 'min', 'maximize', 'minimize']:
        # raise InvalidConfigException('Unknown optimization task')

    if resources is None:
        resources = []
    if discreteResources is None:
        discreteResources = []
    # The topology graph
    topograph = topology.getGraph()

    # Do some sanity checks.
    # Make sure we have at least one path per commodity, otherwise this is
    # infeasible.
    for k in ppk:
        if not ppk[k]:
            raise NoPathsException('No paths for {}, commodity {}'.
                                   format(topology.name, k))

    # Initialize the CPLEX self.cplexproblem
    mainprob = Optimization()
    # Figure out types of constraints we have
    constraints = [x.lower() for x in constraints]
    # Adding basic decision variables
    mainprob.addDecisionVariables(mainprob, ppk)
    # Now lets add all the binary decision variables
    bintypes = []
    if 'requireallnodes' in constraints or 'requiresomenodes' in constraints:
        bintypes.append('node')
        bintypes.append('path')
    if 'requirealledges' in constraints:
        bintypes.append('edge')
        bintypes.append('path')
    if 'dnodecap' in constraints or 'flowsplitting' in constraints:
        bintypes.append('path')
    # Now write  the binary variables
    # print bintypes
    mainprob.addBinaryVariables(mainprob, ppk, topology, bintypes)
    if 'path' in bintypes:
        mainprob.addPathDisable(mainprob, ppk)

    # Now check for any other constraints
    # Write the routing cost
    if 'routingcost' in constraints:
        mainprob.addRoutingCost(mainprob, ppk)
    if 'routeall' in constraints:
        mainprob.addRouteAllConstraints(mainprob, ppk)
    # Setup our link constraints:
    if 'linkcap' in constraints:
        linkcaps = kwargs.get('linkcaps')
        if linkcaps is None:
            linkcaps = {}
            for link in topograph.edges_iter():
                u, v = link
                if 'capacity' in topograph.edge[u][v]:
                    linkcaps[link] = topograph.edge[u][v]['capacity']
        elif isinstance(linkcaps, int) or isinstance(linkcaps, float):
            linkcaps = {link: linkcaps for link in topograph.edges_iter()}
        elif hasattr(linkcaps, '__call__'):
            linkcaps = {link: linkcaps(topology, link) for link in
                        topograph.edges_iter()}
        elif isinstance(linkcaps, dict):
            pass
        mainprob.addLinkConstraints(mainprob, ppk, linkcaps,
                                    maxlink=(
                                        objective.lower() == 'maxlinkload'),
                                    customFunc=kwargs.get('linkcapFunc'))

    def _parseNodeCaps(res):
        mycaps = Tree()
        for r in res:
            # print r
            s = '{}capacity'.format(r)
            tempcaps = kwargs.get(s)
            # print tempcaps
            if tempcaps is None:
                for node in topograph.nodes_iter():
                    if s in topograph.node[node]:
                        mycaps[node][r] = topograph.node[node][s]
            elif isinstance(tempcaps, int) or isinstance(tempcaps, float):
                for node in topograph.nodes_iter():
                    mycaps[node][r] = tempcaps
            elif hasattr(tempcaps, '__call__'):
                for node in topograph.nodes_iter():
                    mycaps[node][r] = tempcaps(topology, node)
            elif isinstance(tempcaps, dict):
                for node in tempcaps:
                    mycaps[node][r] = mycaps[node]
            else:
                raise InvalidConfigException('')
        return mycaps

    # Setup our node load for each node in the topology
    if 'nodecap' in constraints:
        caps = _parseNodeCaps(resources)
        mainprob.addNodeCapacityConstraints(mainprob, ppk, caps,
                                            ('maxload' in objective))
    # Setup discrete loads on switches
    if 'dnodecap' in constraints:
        caps = _parseNodeCaps(discreteResources)
        mainprob.addDiscreteLoadConstraints(mainprob, ppk, caps,
                                            ('maxdload' in objective))
    if 'requireallnodes' in constraints:
        mainprob.addRequireAllNodesConstraints(mainprob, ppk, topograph.nodes())
    elif 'requiresomenodes' in constraints:
        mainprob.addRequireSomeNodesConstraints(mainprob, ppk)
    if 'requirealledges' in constraints:
        mainprob.addRequireAllEdgesConstraint(mainprob, ppk, topograph.edges())
    if 'flowsplitting' in constraints:
        mainprob.addEnforceSinglePath(mainprob, ppk)
    if 'budget' in constraints:
        mainprob.addBudgetConstraint(mainprob, topology, budgetFunc,
                                     budgetBound)
    if 'power' in constraints:
        nc = {n: kwargs.get('switchPower') for n in topograph.nodes_iter()}
        ec = {e: kwargs.get('linkPower') for e in topograph.edges_iter()}
        # print ec
        mainprob.addPowerConstraint(mainprob, nc, ec, normalize=True)
    if 'allocation' in constraints:
        unsat = unsaturatedcomm
        if unsat is not None:
            mainprob.addAllocateFlowConstraints(mainprob, ppk, unsat,
                                                setEqual=True)
            sat = saturatedcomm
            if sat is not None and sat:
                assert len(saturatedcomm) == len(allocationvals)
                if allocationvals is None:
                    raise InvalidConfigException('Allocation values required')
                for index in xrange(len(allocationvals)):
                    mainprob.addAllocateFlowConstraints(mainprob, ppk,
                                                        sat[index],
                                                        allocationvals[index],
                                                        setEqual=True)
        else:
            mainprob.addAllocateFlowConstraints(mainprob, ppk, ppk.keys(),
                                                setEqual=True)
    elif 'demand' in constraints:
        mainprob.addAllocateFlowConstraints(mainprob, ppk, ppk.keys(),
                                            setEqual=False)

    if isinstance(objective, dict):
        mainprob.setObjective(mainprob, objective, task)
    else:
        if objective.lower() == 'routingcost':
            mainprob.setObjective(mainprob, {'RoutingCost': 1}, task)
        elif objective.lower() == 'maxload':
            mainprob.setObjective(mainprob, {'LoadFunction': 1}, task)
        elif objective.lower() == 'maxlinkload':
            mainprob.setObjective(mainprob, {'LinkLoadFunction': 1}, task)
        elif objective.lower() == 'maxloadmaxdload':
            mainprob.setObjective(mainprob,
                                  {'LoadFunction': 1, 'DLoadFunction': 1},
                                  task)
        elif objective.lower() == 'power':
            mainprob.setObjective(mainprob, {'linkpower': 1,
                                             'switchpower': 1}, task)
        elif objective.lower() == 'allocation':
            d = {n: 1 for n in mainprob.variables.get_names()
                 if n.startswith('allocation')}
            mainprob.setObjective(mainprob, d, task)
        elif objective.lower() == 'throughput':
            d = {n: 1 / topology.getNumFlows()
                 for n in mainprob.variables.get_names()
                 if n.startswith('allocation')}
            mainprob.setObjective(mainprob, d, task)
        else:
            raise InvalidConfigException('Unknown objective')
    if 'mindiff' in constraints:
        prevSolution = kwargs.get('prevSolution')
        mainprob.addMinDiffConstraints(mainprob, prevSolution,
                                       diffFactor=diffFactor)

    if mipgap is not None:
        mainprob.parameters.mip.tolerances.mipgap.set(mipgap)
    mainprob.set_log_stream(None)
    mainprob.set_results_stream(None)
    if timelimit is not None:
        mainprob.parameters.timelimit.set(timelimit)
    return mainprob


# def _MaxMinFairness_mcf(topology, unsat, sat, alloc, ppk):
# """ Formulate and solve a multi-commodity flow self.cplexproblem given the saturated
# and un-saturated commodities
#
# :param topology
# :returns: allocations and the cplex solved self.cplexproblem (for variable access)"""
# self.cplexprob = generateFormulation(topology, ppk,
# constraints=['allocation'],
# objective='allocation', task='max',
# unsaturatedcomm=unsat,
# saturatedcomm=sat,
# allocationvals=alloc)
# self.cplexprob.solve()
# alloc = self.cplexprob.solution.get_objective_value()
# return alloc, self.cplexprob


# def iterateMaxMinFairness(topology, pptc):
#     """ Run the iterative algorithm for max-min fairness
#
#        ..warning:: This implementation does not use any optimizations
#            like binary search
#
#        :param topology: the topology on which we are running this
#        :param pptc: paths per commodity
#        :return: a tuple: solved CPLEX self.cplexproblem and a dict containing
#            allocation values per commodity
#        :rtype: tuple
#     """
#     commoditiesSAT = defaultdict(lambda: [])
#     commoditiesUNSAT = set(pptc.keys())
#     self.cplexprob = None
#     t = []  # allocation values per each iteration
#     i = 0  # iteration index
#     while commoditiesUNSAT:
#         print i,
#         alloc, self.cplexprob = _MaxMinFairness_mcf(topology, commoditiesUNSAT,
#                                                     commoditiesSAT, t, pptc)
#         if not self.cplexprob.solution.get_status() == 1:
#             raise UnsupportedOperationException(
#                 'No solution to the self.cplexproblem')
#         t.append(alloc)
#         # Check if commodity is saturated, if so move it to saturated list
#         for k in list(commoditiesUNSAT):
#             # FIXME: this is a very inefficient non-blocking test
#             dual = self.cplexprob.solution.get_dual_values(
#                 'Demand.k.{}'.format(k.ID))
#             if dual > 0:
#                 commoditiesUNSAT.remove(k)
#                 commoditiesSAT[i].append(k)
#         i += 1
#     print i
#     # Simplify the result
#     result = {}
#     for j in xrange(len(t)):
#         for k in commoditiesSAT[j]:
#             result[k] = t[j]
#     return self.cplexprob, result
