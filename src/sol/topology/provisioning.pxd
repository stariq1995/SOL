# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool
from tmgen cimport TrafficMatrix

cdef compute_background_load(Topology topology, trafficClasses)
cpdef traffic_classes(TrafficMatrix tm, dict fractions, dict class_bytes,
                      as_dict= *)
cpdef provision_links(Topology topology, list traffic_classes,
                      float overprovision= *, bool set_attr= *)
