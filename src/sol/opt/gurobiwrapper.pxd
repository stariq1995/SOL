# coding=utf-8

from sol.path.paths cimport Path
from sol.topology.traffic cimport TrafficClass
from sol.topology.topology cimport Topology

cdef class OptimizationGurobi:

    cdef public opt
    cdef dict expressions

    cpdef addDecisionVars(self, dict pptc)
    cpdef addBinaryVars(self, dict pptc, Topology topology, vtypes)
    cpdef allocateFlow(self, pptc, allocation=*)
    cdef _dumpExpressions(self)
    cpdef solve(self)
    cpdef getPathFractions(self, pptc, flowCarryingOnly=*)