# coding=utf-8

from sol.topology.topology cimport Topology

cpdef provisionLinks(Topology topology, list trafficClasses, float overprovision= *, setAttr= *)
# cpdef uniformTM(iepairs, double totalFlows)
cpdef generateIEpairs(topology)
# cpdef logNormalTM(iepairs, meanFlows)
# cpdef gravityTM(iepairs, double totalFlows, populationDict)
cdef computeBackgroundLoad(Topology topology, trafficClasses)