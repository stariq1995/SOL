# coding=utf-8
from sol.optimization.formulation.cplex import OptimizationCPLEX
from sol.optimization.formulation.gurobi import OptimizationGurobi
from sol.optimization.path.generate import generatePathsPerIE
from sol.optimization.path.predicates import nullPredicate
from sol.optimization.path.select import getSelectFunction
from sol.optimization.topology.topology import Topology
from sol.util.exceptions import InvalidConfigException, NoPathsException


CPLEX = 'cplex'
GUROBI = 'gurobi'
DEFAULT_OPTIMIZER = CPLEX


def getOptimization(backend=DEFAULT_OPTIMIZER):
    """
    Return an optimization object that implements the interfce to a given backend.

    :param backend: optiimization backend. Currently 'CPLEX' and 'Gurobi' are supported
    :return: the :py:class:`Optimization` object
    :raise InvalidConfigException: if the backend provided is not supported
    """
    if backend == CPLEX:
        return OptimizationCPLEX()
    elif backend == GUROBI:
        return OptimizationGurobi()
    else:
        raise InvalidConfigException('Unsupported optimization backend')


def generateFormulation(topology=None, pptc=None,
                        trafficClasses=None,
                        constraints=None,
                        objective=None, nodeResources=None, linkResources=None,
                        nodeCapFunction=None, linkCapFunction=None,
                        budgetBound=None, budgetFunc=None,
                        allocationvals=None, saturatedcomm=None,
                        unsaturatedcomm=None,
                        mipgap=None, timelimit=None,
                        diffFactor=0,
                        selectStrategy=None, selectNumber=None,
                        maxPathLength=float('inf'), predicate=nullPredicate, nodeCaps=None,
                        linkCaps=None, prevSolution=None, name=None, **kwargs):
    """Generate the formulation based on the high-level configuration

    :param topology:
    :param pptc:
    :param trafficClasses:
    :param constraints:
    :param objective:
    :param nodeResources:
    :param linkResources:
    :param nodeCapFunction:
    :param linkCapFunction:
    :param budgetBound:
    :param budgetFunc:
    :param allocationvals:
    :param saturatedcomm:
    :param unsaturatedcomm:
    :param mipgap:
    :param timelimit:
    :param topology: the topology on which we are running
    :param pptc: paths per traffic class
    :param kwargs: all other keyword arguments
    :return: The :py:class:`~optbase.Optimization` object
    """

    if topology is None:
        raise InvalidConfigException("No topology specified")
    if isinstance(topology, str):
        toponame = topology
        topology = Topology(toponame, graph=toponame)
    else:
        topograph = topology.getGraph()

    if pptc is None:
        pptc = {}
        for tc in trafficClasses:
            i, e = tc.getIEPair()
            # TODO: come up with better way of path modification
            pptc[tc] = generatePathsPerIE(i, e, topology, predicate,
                                          maxPathLength, modifyFunc=kwargs.get('pathModifier'))
        if selectNumber is not None:
            selectFunc = getSelectFunction(selectStrategy)
            pptc = selectFunc(pptc, selectNumber)

    # Make sure we have at least one path per commodity, otherwise this is
    # infeasible.
    for tc in pptc:
        if not pptc[tc]:
            raise NoPathsException('No paths for {}, commodity {}'.
                                   format(topology.name, tc))
    # TODO: perform better input validation. nodeCapFunction, linkCapFunction must be callable

    # Initialize the optimization
    mainprob = getOptimization()
    if name is not None and hasattr(mainprob, 'setName'):
        mainprob.setName(name)


    # Figure out types of constraints we have
    constraintNames = []
    for const in constraints:
        if isinstance(const, tuple):
            if isinstance(const[0], str):
                constraintNames.append(const[0].lower())
            else:
                raise InvalidConfigException('Unsupported constraint type')
        elif isinstance(const, str):
            constraintNames.append(const.lower())
        else:
            raise InvalidConfigException('Unsupported constraint type')

    # Adding basic decision variables
    mainprob.addDecisionVariables(pptc)
    # Now lets add all the binary decision variables
    # Let's try and not add unnecessary variables. Add binaries if constraints are present
    bintypes = []
    if 'requireallnodes' in constraintNames or 'requiresomenodes' in constraintNames:
        bintypes.append('node')
        bintypes.append('path')
    if 'requirealledges' in constraintNames:
        bintypes.append('edge')
        bintypes.append('path')
    if 'nodecapifactive' in constraintNames or 'requiresinglepath' in constraintNames:
        bintypes.append('path')
    mainprob.addBinaryVariables(pptc, topology, bintypes)
    if 'path' in bintypes:
        mainprob.addPathDisableConstraint(pptc, pptc.keys())

    # Iterate over the constraints and construct the formulation
    for index, constraint in enumerate(constraintNames):
        if constraint == 'routingcost':
            mainprob.addRoutingCost(pptc)
        if constraint == 'allocateflow':
            mainprob.addAllocateFlowConstraint(pptc)
        if 'routeall' == constraint:
            mainprob.addRouteAllConstraint(pptc)
        if 'linkcap' == constraint:
            resource = constraints[index][1]
            mainprob.addLinkCapacityConstraint(pptc, resource, linkCaps,
                                                linkCapFunction)
        if 'nodecap' == constraint:
            resource = constraints[index][1]
            mainprob.addNodeCapacityConstraint(pptc, resource, nodeCaps,
                                                nodeCapFunction)
        if 'nodecapifactive' == constraint:
            nodecaps = nodeCaps
            resource = constraints[index][1]
            mainprob.addNodeCapacityIfActive(pptc, resource, nodecaps,
                                             nodeCapFunction)
        if 'requireallnodes' == constraint:
            mainprob.addRequireAllNodesConstraint(pptc,
                                                   topograph.nodes())
        if 'requiresomenodes' in constraints:
            mainprob.addRequireSomeNodesConstraint(pptc)
        if 'requirealledges' in constraints:
            mainprob.addRequireAllEdgesConstraint(pptc,
                                                  topograph.edges())
        if 'onepath' in constraints:
            mainprob.addEnforceSinglePath(pptc)
        if 'budget' in constraints:
            mainprob.addBudgetConstraint(topology, budgetFunc,
                                         budgetBound)


    # if 'power' in constraints:
    # nc = {n: kwargs.get('switchPower') for n in topograph.nodes_iter()}
    # ec = {e: kwargs.get('linkPower') for e in topograph.edges_iter()}
    # # print ec
    # mainprob.addPowerConstraint(mainprob, nc, ec, normalize=True)
    # if 'allocation' in constraints:
    # unsat = unsaturatedcomm
    # if unsat is not None:
    #         mainprob.addAllocateFlowConstraints(mainprob, pptc, unsat,
    #                                             setEqual=True)
    #         sat = saturatedcomm
    #         if sat is not None and sat:
    #             assert len(saturatedcomm) == len(allocationvals)
    #             if allocationvals is None:
    #                 raise InvalidConfigException('Allocation values required')
    #             for index in xrange(len(allocationvals)):
    #                 mainprob.addAllocateFlowConstraints(mainprob, pptc,
    #                                                     sat[index],
    #                                                     allocationvals[index],
    #                                                     setEqual=True)
    #     else:
    #         mainprob.addAllocateFlowConstraints(mainprob, pptc, pptc.keys(),
    #                                             setEqual=True)
    # elif 'demand' in constraints:
    #     mainprob.addAllocateFlowConstraints(mainprob, pptc, pptc.keys(),
    #                                         setEqual=False)

    # if isinstance(objective, dict):
    #     mainprob.setObjective(mainprob, objective, task)
    # else:
    #     if objective.lower() == 'routingcost':
    #         mainprob.setObjective(mainprob, {'RoutingCost': 1}, task)
    #     elif objective.lower() == 'maxload':
    #         mainprob.setObjective(mainprob, {'LoadFunction': 1}, task)
    #     elif objective.lower() == 'maxlinkload':
    #         mainprob.setObjective(mainprob, {'LinkLoadFunction': 1}, task)
    #     elif objective.lower() == 'maxloadmaxdload':
    #         mainprob.setObjective(mainprob,
    #                               {'LoadFunction': 1, 'DLoadFunction': 1},
    #                               task)
    #     elif objective.lower() == 'power':
    #         mainprob.setObjective(mainprob, {'linkpower': 1,
    #                                          'switchpower': 1}, task)
    #     elif objective.lower() == 'allocation':
    #         d = {n: 1 for n in mainprob.variables.get_names()
    #              if n.startswith('allocation')}
    #         mainprob.setObjective(mainprob, d, task)
    #     elif objective.lower() == 'throughput':
    #         d = {n: 1 / topology.getNumFlows()
    #              for n in mainprob.variables.get_names()
    #              if n.startswith('allocation')}
    #         mainprob.setObjective(mainprob, d, task)
    #     else:
    #         raise InvalidConfigException('Unknown objective')

    if objective is not None:
        if isinstance(objective, str):
            mainprob.setPredefinedObjective(objective)
        elif isinstance(objective, tuple):
            mainprob.setPredefinedObjective(*objective)
        else:
            raise InvalidConfigException('Unsupported objective function')
    if 'mindiff' in constraintNames:
        prevSolution = prevSolution
        if prevSolution is None:
            raise InvalidConfigException('Must specify prevSolution with '
                                         'mindiff constraint')
        mainprob.addMinDiffConstraint(mainprob, prevSolution,
                                       diffFactor=diffFactor)

    #TODO: add mipgap/timelimit
    # if mipgap is not None:
    #     mainprob.parameters.mip.tolerances.mipgap.set(mipgap)
    # if timelimit is not None:
    #     mainprob.parameters.timelimit.set(timelimit)
    return mainprob, pptc

# TODO: bring back max-min fairness
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
# """ Run the iterative algorithm for max-min fairness
#
# ..warning:: This implementation does not use any optimizations
# like binary search
#
# :param topology: the topology on which we are running this
# :param pptc: paths per commodity
# :return: a tuple: solved CPLEX self.cplexproblem and a dict containing
# allocation values per commodity
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
#             # TODO: this is a very inefficient non-blocking test
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
