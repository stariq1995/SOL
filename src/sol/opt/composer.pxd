# coding=utf-8
from sol.topology.topology cimport Topology

cpdef compose(list apps, Topology topo)
cdef addNamedConstraints(opt, app)
cpdef detectCostConflict(list apps)
cpdef addObjVar(app, Topology topo, opt, double weight=*)
# cpdef getObjVar(app, Topology opt, value=*)