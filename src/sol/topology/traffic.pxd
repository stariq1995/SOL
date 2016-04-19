# coding=utf-8

cdef class TrafficClass:
    cdef public int ID, priority, src, dst
    cdef public str name
    cdef public double volFlows, volBytes
    cdef public srcIPPrefix, dstIPPrefix, srcAppPorts, dstAppPorts