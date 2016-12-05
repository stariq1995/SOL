# coding=utf-8

__all__ = ['get_optimization', 'from_app']

from sol.utils.const import DEFAULT_OPTIMIZER, CPLEX, GUROBI
from gurobiwrapper cimport OptimizationGurobi, add_named_constraints, \
    add_obj_var
from sol.utils.exceptions import InvalidConfigException

def get_optimization(backend=DEFAULT_OPTIMIZER):
    """
    Return an optimization object that implements the interfce to a given backend.

    :param backend: optimization backend. Currently 'CPLEX' are supported. Gurobi is planned
    :return: the :py:class:`~Optimization` object
    :raise InvalidConfigException: if the provided backend is not supported
    """
    if backend.lower() == CPLEX:
        raise NotImplementedError('No longer supported')
        # return OptimizationCPLEX()
    elif backend.lower() == GUROBI:
        from gurobiwrapper import OptimizationGurobi
        return OptimizationGurobi()
    else:
        raise InvalidConfigException('Unsupported optimization backend')


# def initOptimization(topology, trafficClasses, predicate=null_predicate,
#                      selectStrategy='shortest', selectNumber=10,
#                      modifyFunc=None, backend=DEFAULT_OPTIMIZER):
#     """
#     A kick start function for the optimization
#
#     Generates the paths for the traffic classes, automatically selects the paths based on given numbers and strategy,
#     and by default adds the decision variables
#
#     :param topology: topology we are working with
#     :param trafficClasses: a list of traffic classes
#     :param predicate: the predicate to verify path validity
#     :param selectStrategy: way to select paths ('random', 'shortest'...)
#     :param selectNumber: number of paths per traffic class to choose
#     :param modifyFunc: the path modifier function
#     :param backend: the optimization backend
#     :return: a tuple containing the :py:class:`~sol.optimization.optbase.Optimization` object and paths per traffic class
#         (in the form of a dictionary)
#     """
#     opt = get_optimization(backend)
#     pptc = generate_paths_tc(topology, trafficClasses, predicate,
#                                         networkx.diameter(topology.get_graph()) * 1.5,
#                                         modifyFunc=modifyFunc)
#     selectFunc = get_select_function(selectStrategy)
#     pptc = selectFunc(pptc, selectNumber)
#     opt._add_decision_vars(pptc)
#     return opt, pptc

cpdef from_app(topo, app, backend=GUROBI):
    opt = OptimizationGurobi(topo, app.pptc)
    add_named_constraints(opt, app)
    node_caps = {node: topo.get_resources(node) for node in topo.nodes()}
    link_caps = {link: topo.get_resources(link) for link in topo.links()}
    for r in app.resourceCost:
        opt.consume(app.pptc, r, app.resourceCost[r],
                    {n: node_caps[n][r] for n in node_caps if
                     r in node_caps[n]},
                    {l: link_caps[l][r] for l in link_caps if
                     r in link_caps[l]})
    add_named_constraints(opt, app)
    # for r in app.resourceCost.keys():
    #     opt.cap(r, 1)
    add_obj_var(app, opt, weight=1)
    return opt
