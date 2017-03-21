# coding=utf-8

from sol.topology.traffic cimport TrafficClass
from sol.path.paths cimport Path

cpdef unicode xp(TrafficClass traffic_class, int path_index, int epoch)
cpdef unicode al(TrafficClass traffic_class, int epoch)
cpdef unicode bn(int node)
cpdef unicode be(int head, int tail)
cpdef unicode bp(TrafficClass traffic_class, int path_index)
# cpdef unicode nl(int node, unicode resource, int epoch=*)
# cpdef unicode el(tuple link, unicode resource, int epoch=*)
# cpdef unicode nc(int node, unicode resource, int epoch=*)