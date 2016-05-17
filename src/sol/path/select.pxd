# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool

cpdef choose_rand(dict pptc, int num_paths)
cpdef sort_paths_per_commodity(dict pptc, key=*, bool inplace=*)
cpdef select_robust(apps, Topology topo)
# cdef _merge_pptc(apps)
# cdef _filter_pptc(apps, chosen_pptc)