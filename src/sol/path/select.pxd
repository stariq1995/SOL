# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool

cpdef choose_rand(dict pptc, int num_paths)
cpdef sort_paths_per_commodity(dict pptc, key=*, bool inplace=*)
cpdef select_ilp(apps, Topology topo, int num_paths=*, debug=*, mode=*)
cpdef merge_pptc(apps, sort=*, key=*)
cpdef select_sa(apps, Topology topo, int num_paths=*, int max_iter=*,
                double tstart=*, double c=*, logdb=*, mode=*)
# cdef _filter_pptc(apps, chosen_pptc)