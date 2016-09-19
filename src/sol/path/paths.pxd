# coding=utf-8
import numpy
cimport numpy
from cpython cimport bool

# noinspection PyClassicStyleClass
cdef class Path:
    cdef int _ID
    cdef public double _flowFraction
    cdef public numpy.ndarray _nodes
    cdef _links

    cpdef int ingress(self)
    cpdef int egress(self)
    cdef _compute_links(self)
    cpdef tuple iepair(self)
    cpdef double flow_fraction(self)
    cpdef set_flow_fraction(self, double f)
    cpdef links(self)
    cpdef nodes(self)
    cpdef int get_id(self)
    cpdef dict encode(self)

# noinspection PyClassicStyleClass
cdef class PathWithMbox(Path):
    cdef public list useMBoxes

    cpdef dict encode(self)
    cpdef bool uses_box(self, node)
