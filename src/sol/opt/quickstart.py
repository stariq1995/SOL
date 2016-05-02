# coding=utf-8
import networkx

from sol.opt.varnames import DEFAULT_OPTIMIZER, CPLEX, GUROBI
from sol.path.generate import generatePathsPerTrafficClass
from sol.path.select import get_select_function
from sol.path.predicates import nullPredicate
from sol.utils.exceptions import InvalidConfigException


def getOptimization(backend=DEFAULT_OPTIMIZER):
    """
    Return an optimization object that implements the interfce to a given backend.

    :param backend: optimization backend. Currently 'CPLEX' are supported. Gurobi is planned
    :return: the :py:class:`~Optimization` object
    :raise InvalidConfigException: if the provided backend is not supported
    """
    if backend.lower() == CPLEX:
        from cplexwrapper import OptimizationCPLEX
        return OptimizationCPLEX()
    elif backend.lower() == GUROBI:
        from gurobiwrapper import OptimizationGurobi
        return OptimizationGurobi()
    else:
        raise InvalidConfigException('Unsupported optimization backend')


def initOptimization(topology, trafficClasses, predicate=nullPredicate, selectStrategy='shortest', selectNumber=10,
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
    pptc = generatePathsPerTrafficClass(topology, trafficClasses, predicate,
                                        networkx.diameter(topology.get_graph()) * 1.5,
                                        modifyFunc=modifyFunc)
    selectFunc = get_select_function(selectStrategy)
    pptc = selectFunc(pptc, selectNumber)
    opt._add_decision_vars(pptc)
    return opt, pptc
