# coding=utf-8

from sol.topology.topology cimport Topology

cpdef choose_rand(dict pptc, int num_paths)
cpdef sort_paths_per_commodity(dict pptc, key=None, bool inplace=True)
cpdef select_optimal(apps, Topology topo)
cpdef select_robust(apps, Topology topo)
