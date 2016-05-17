# coding=utf-8

from sol.topology.traffic cimport TrafficClass
from sol.path.paths cimport Path

cpdef str xp(TrafficClass traffic_class, Path path, int epoch=*)
cpdef str al(TrafficClass traffic_class, int epoch=*)
cpdef str bn(int node)
cpdef str be(int head, int tail)
cpdef str bp(TrafficClass traffic_class, Path path)
cpdef str nl(int node, str resource, int epoch=*)
cpdef str el(tuple link, str resource, int epoch=*)
cpdef str nc(int node, str resource, int epoch=*)