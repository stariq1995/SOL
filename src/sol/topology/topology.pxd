# coding=utf-8

# noinspection PyClassicStyleClass
cdef class Topology:
    cdef public str name
    cdef public _graph

    cpdef dict get_resources(self, nodeOrLink)
    cpdef nodes(self, data=*)
    cpdef edges(self, data=*)