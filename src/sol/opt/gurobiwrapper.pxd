# coding=utf-8

from sol.path.paths cimport Path
from sol.topology.traffic cimport TrafficClass
from sol.topology.topology cimport Topology

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:

    cdef public opt
    cdef dict expressions

    cpdef addDecisionVars(self, dict pptc)
    cpdef addBinaryVars(self, dict pptc, vtypes)
    cpdef allocateFlow(self, pptc, allocation=*)
    cpdef solve(self)
    cpdef getPathFractions(self, pptc, flowCarryingOnly=*)
    cpdef route_all(self, pptc)
    cpdef getSolvedObjective(self)
    cpdef isSolved(self)
    cpdef v(self, n)
    cpdef get_chosen_paths(self, pptc)
    cdef _dump_expressions(self)

