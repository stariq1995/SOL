# coding=utf-8
import numpy
cimport numpy
from cpython cimport bool

# noinspection PyClassicStyleClass
from sol.topology.traffic cimport TrafficClass

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
    cpdef bool uses_box(self, node)

# noinspection PyClassicStyleClass
cdef class PathWithMbox(Path):
    cdef public list useMBoxes

    cpdef dict encode(self)
    cpdef bool uses_box(self, node)

cdef class PPTC:
    cdef public _data #TODO: does this need to be public
    cdef public _tcindex
    cdef public _name_to_tcs
    cdef public _tcowner
    cpdef add(self, name, TrafficClass tc, paths)
    cpdef tcs(self, name=*)
    cpdef paths(self, TrafficClass tc)
    cpdef PPTC pptc(self, name)
    cpdef mask(self, TrafficClass tc, mask)
    cpdef unmask(self, TrafficClass tc)
    cpdef clear_masks(self)
    cpdef update(self, PPTC other)
    cpdef copy(self)
    cpdef TrafficClass tc_byid(self, int tcid)
    cpdef int max_paths(self)
    cpdef int num_tcs(self)
    cpdef int total_paths(self)
    cpdef int num_paths(self, tc)