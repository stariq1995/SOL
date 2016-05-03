# coding=utf-8

from sol.topology.topology cimport Topology
from cpython cimport bool

cpdef provision_links(Topology topology, list traffic_classes,
                      float overprovision=3, bool set_attr=*)
# cpdef uniformTM(iepairs, double totalFlows)
cpdef generateIEpairs(topology)
# cpdef logNormalTM(iepairs, meanFlows)
# cpdef gravityTM(iepairs, double totalFlows, populationDict)
cdef computeBackgroundLoad(Topology topology, trafficClasses)