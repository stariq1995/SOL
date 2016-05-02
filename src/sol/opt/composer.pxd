# coding=utf-8
from sol.topology.topology cimport Topology

cpdef compose(list apps, Topology topo)
cdef add_named_constraints(opt, app)
cpdef _detect_cost_conflict(list apps)
cpdef add_obj_var(app, Topology topo, opt, double weight=*)