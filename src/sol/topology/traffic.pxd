# coding=utf-8

import numpy as np
cimport numpy as np

# noinspection PyClassicStyleClass
cdef class TrafficClass:
    cdef public int ID, priority, src, dst
    cdef public str name
    cdef public np.ndarray volFlows, volBytes
    cdef public srcIPPrefix, dstIPPrefix, srcAppPorts, dstAppPorts