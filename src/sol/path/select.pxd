# coding=utf-8

from sol.topology.topology cimport Topology
from tmgen.tm cimport TrafficMatrix

cpdef choose_rand(dict pptc, int num_paths)
cpdef sort_paths_per_commodity(dict pptc, key=*, bool inplace=*)
cpdef select_robust(apps, Topology topo)
cpdef traffic_classes(TrafficMatrix tm, fractions, class_bytes, as_dict=*)