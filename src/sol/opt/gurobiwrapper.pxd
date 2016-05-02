# coding=utf-8

from sol.path.paths cimport Path
from sol.topology.traffic cimport TrafficClass
from sol.topology.topology cimport Topology

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:

    cdef public opt
    cdef dict expressions

    cpdef _add_decision_vars(self, dict pptc)
    cpdef _add_binary_vars(self, dict pptc, vtypes)
    cpdef allocate_flow(self, pptc, allocation=*)
    cpdef solve(self)
    cpdef get_path_fractions(self, pptc, flowCarryingOnly=*)
    cpdef route_all(self, pptc)
    cpdef get_solved_objective(self)
    cpdef is_solved(self)
    cpdef v(self, n)
    cpdef get_chosen_paths(self, pptc)
    cdef _dump_expressions(self)
    cpdef set_time_limit(self, long time)

