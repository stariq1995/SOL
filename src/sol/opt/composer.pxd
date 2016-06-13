# coding=utf-8
from sol.topology.topologynx cimport Topology
from cpython cimport bool

cpdef compose(list apps, Topology topo, epoch_mode=*)
# cdef add_named_constraints(opt, app)
cpdef _detect_cost_conflict(apps)
