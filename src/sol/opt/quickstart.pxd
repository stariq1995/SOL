# coding=utf-8

from sol.topology.topologynx cimport Topology
from .app cimport App

cpdef from_app(Topology topo, App app, network_config)
