# coding=utf-8

from sol.topology.traffic cimport TrafficClass
from sol.path.paths cimport Path

cpdef xp(TrafficClass trafficClass, Path path)
cpdef al(TrafficClass trafficClass)
cpdef bn(int node)
cpdef be(int head, int tail)
cpdef bp(TrafficClass trafficClass, Path path)
cpdef nl(int node, str resource)
cpdef el(tuple link, str resource)
cpdef nc(int node, str resource)