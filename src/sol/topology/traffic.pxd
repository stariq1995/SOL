# coding=utf-8

import numpy as np
cimport numpy as np

# noinspection PyClassicStyleClass
cdef class TrafficClass:
    cdef public int ID, priority, src, dst
    cdef public unicode name
    cdef public np.ndarray volFlows, volBytes
    cdef public srcIPPrefix, dstIPPrefix, srcAppPorts, dstAppPorts

    cpdef tuple iepair(self)
    cpdef int ingress(self)
    cpdef int egress(self)