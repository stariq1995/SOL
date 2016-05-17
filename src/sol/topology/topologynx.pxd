# coding=utf-8

from cpython cimport bool

# noinspection PyClassicStyleClass
cdef class Topology:
    cdef public str name
    cdef public _graph

    cdef _process_graph(self)
    cpdef num_nodes(self, str service=*)
    cpdef get_graph(self)
    cpdef set_graph(self, graph)
    cpdef dict get_resources(self, nodeOrLink)
    cpdef nodes(self, data=*)
    cpdef edges(self, data=*)
    cpdef get_service_types(self, node)
    cpdef set_service_types(self, node, service_types)
    cpdef add_service_type(self, node, service_type)
    cpdef set_resource(self, node_or_link, str resource, double capacity)
    cpdef dict get_resources(self, node_or_link)
    cpdef bool has_middlebox(self, node)
    cpdef set_middlebox(self, node, val=*)