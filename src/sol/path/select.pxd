# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool

from sol.path.paths cimport PPTC

cpdef choose_rand(PPTC pptc, int num_paths)
cpdef k_shortest_paths(PPTC pptc, int num_paths, bool ret_mask=*)
cpdef select_ilp(apps, Topology topo, network_config, int num_paths, debug=*,
                 fairness=*, epoch_mode=*)
cpdef select_sa(apps, Topology topo, network_config, int num_paths=*, int max_iter=*,
                double tstart=*, double c=*,
                fairness=*, epoch_mode=*, expel_mode=*, replace_mode=*,
                resource_weights=*, cb=*, select_config=*, debug=*)
cpdef select_iterative(apps, topo, network_config, max_iter, epsilon, fairness, epoch_mode, sort_mode=*, debug=*)
