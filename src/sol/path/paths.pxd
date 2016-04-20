# coding=utf-8

from sol.topology.topology cimport Topology

cdef class Path:
    cdef public int _ID
    cdef public double _flowFraction
    cdef public _nodes
    cdef _links

    cpdef int getIngress(self)
    cpdef int getEgress(self)
    cdef _computeLinks(self)
    cpdef tuple getIEPair(self)
    cpdef double getFlowFraction(self)
    cpdef setFlowFraction(self, double nflows)
    cpdef getLinks(self)
    cpdef getNodes(self)
    cpdef int getID(self)

cdef class PathWithMbox(Path):
    cdef public list useMBoxes

cdef double computePathCapacity(Path p, str resourceName, Topology topo)