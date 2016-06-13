# coding=utf-8

from cpython cimport bool
from sol.topology.topologynx cimport Topology

cpdef use_mbox_modifier(path, int offset, Topology topology, chain_length= *)
cpdef generate_paths_ie(int source, int sink, Topology topology, predicate,
                        int cutoff, float max_paths= *, modify_func= *,
                        bool raise_on_empty= *)
cpdef generate_paths_tc(Topology topology, traffic_classes, predicate, cutoff,
                        max_paths= *, modify_func= *,
                        raise_on_empty= *)
