# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool

from sol.path.paths cimport PPTC

cpdef choose_rand(PPTC pptc, int num_paths)
# cpdef sort_paths(pptc, key=*, bool inplace=*)
cpdef select_ilp(apps, Topology topo, int num_paths=*, debug=*, mode=*, globalcaps=*)
# cpdef merge_pptc(apps, sort=*, key=*)
cpdef select_sa(apps, Topology topo, int num_paths=*, int max_iter=*,
                double tstart=*, double c=*, logdb=*, mode=*,
                expel_mode=*, replace_mode=*, select_config=*, globalcaps=*,
                debug=*)
cpdef k_shortest_paths(PPTC pptc, int num_paths, bool ret_mask=*)

