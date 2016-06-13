# coding=utf-8

from sol.topology.topologynx cimport Topology

cpdef null_predicate(path, topology=*)
cpdef has_mbox_predicate(path, Topology topology)
cpdef waypoint_mbox_predicate(path, Topology topology, order)
