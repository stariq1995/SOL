# coding=utf-8

from sol.topology.topology cimport Topology

cpdef inline nullPredicate(path, topology=*)
cpdef useMboxModifier(path, int offset, Topology topology, chainLength=*)
cpdef hasMboxPredicate(path, Topology topology)
cpdef waypointMboxPredicate(path, Topology topology, order)
