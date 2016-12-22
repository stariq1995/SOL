# coding=utf-8
from sol.topology.topologynx cimport Topology

cpdef compose(list apps, Topology topo, epoch_mode=*, obj_mode=*, globalcaps=*)
# cdef add_named_constraints(opt, app)
cpdef _detect_cost_conflict(apps)
