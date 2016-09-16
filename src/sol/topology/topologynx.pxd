# coding=utf-8

from cpython cimport bool

# noinspection PyClassicStyleClass
cdef class Topology:
    cdef public unicode name
    cdef public _graph

    cdef _process_graph(self)
    cpdef num_nodes(self, unicode service=*)
    cpdef get_graph(self)
    cpdef set_graph(self, graph)
    cpdef dict get_resources(self, nodeOrLink)
    cpdef nodes(self, data=*)
    cpdef edges(self, data=*)
    cpdef links(self, data=*)
    cpdef get_service_types(self, int node)
    cpdef set_service_types(self, int node, service_types)
    cpdef add_service_type(self, int node, service_type)
    cpdef set_resource(self, node_or_link, unicode resource, double capacity)
    cpdef dict get_resources(self, node_or_link)
    cpdef bool has_middlebox(self, int node)
    cpdef bool has_mbox(self, int node)
    cpdef set_middlebox(self, int node, val=*)
    cpdef set_mbox(self, int node, val=*)
    cpdef int diameter(self)
    cpdef bool is_leaf(self, int node)
    cpdef paths(self, int source, int sink, int cutoff)
