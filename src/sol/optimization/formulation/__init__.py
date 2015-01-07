# coding=utf-8
import networkx
from sol.optimization.formulation.cplexwrapper import OptimizationCPLEX
from sol.optimization.formulation.gurobiwrapper import OptimizationGurobi
from sol.optimization.path.generate import generatePathsPerTrafficClass
from sol.optimization.path.select import getSelectFunction
from sol.utils.exceptions import InvalidConfigException

CPLEX = 'cplex'
GUROBI = 'gurobi'
DEFAULT_OPTIMIZER = CPLEX


def getOptimization(backend=DEFAULT_OPTIMIZER):
    """
    Return an optimization object that implements the interfce to a given backend.

    :param backend: optimization backend. Currently 'CPLEX' are supported. Gurobi is planned
    :return: the :py:class:`~Optimization` object
    :raise InvalidConfigException: if the provided backend is not supported
    """
    if backend == CPLEX:
        return OptimizationCPLEX()
    elif backend == GUROBI:
        return OptimizationGurobi()
    else:
        raise InvalidConfigException('Unsupported optimization backend')


def kickStartOptimization(topology, trafficClasses, predicate, selectStrategy, selectNumber=None,
                          modifyFunc=None, backend=DEFAULT_OPTIMIZER):
    """
    A kick start function for the optimization

    Generates the paths for the traffic classes, automatically selects the paths based on given numbers and strategy,
    and by default adds the decision variables

    :param topology: topology we are working with
    :param trafficClasses: a list of traffic classes
    :param predicate: the predicate to verify path validity
    :param selectStrategy: way to select paths ('random', 'shortest'...)
    :param selectNumber: number of paths per traffic class to choose
    :param modifyFunc: the path modifier function
    :param backend: the optimization backend
    :return: a tuple containing the :py:class:`~sol.optimization.optbase.Optimization` object and paths per traffic class
        (in the form of a dictionary)
    """
    opt = getOptimization(backend)
    pptc = generatePathsPerTrafficClass(topology, trafficClasses, predicate, networkx.diameter(topology.getGraph())*1.5,
                                        modifyFunc=modifyFunc)
    selectFunc = getSelectFunction(selectStrategy)
    pptc = selectFunc(pptc, selectNumber)
    opt.addDecisionVariables(pptc)
    return opt, pptc


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
