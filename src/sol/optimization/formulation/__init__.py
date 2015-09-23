# coding=utf-8
import networkx
from sol.optimization.formulation.cplexwrapper import OptimizationCPLEX
from sol.optimization.formulation.gurobiwrapper import OptimizationGurobi
from sol.optimization.path.generate import generatePathsPerTrafficClass
from sol.optimization.path.predicates import nullPredicate
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
    if backend.lower() == CPLEX:
        return OptimizationCPLEX()
    elif backend.lower() == GUROBI:
        return OptimizationGurobi()
    else:
        raise InvalidConfigException('Unsupported optimization backend')


def kickStartOptimization(topology, trafficClasses, predicate=nullPredicate, selectStrategy='shortest', selectNumber=10,
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
