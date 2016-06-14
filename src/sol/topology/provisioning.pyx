# coding=utf-8
from __future__ import division

import networkx
from sol.topology.traffic cimport TrafficClass
from sol.topology.topologynx cimport Topology
from tmgen cimport TrafficMatrix
from six import iteritems, iterkeys
from six.moves import range, zip
from cpython cimport bool
from sol.opt.varnames import BANDWIDTH
import numpy as np
cimport numpy as np

# cpdef generateIEpairs(topology):
#     """
#     Default way of generating ingress-egress pairs. Generates all possible n*(n-1) node combinations
#
#     :param topology: the topology to work with
#     :type topology: sol.optimization.topology.topology
#     :return: list of ingress-egress pairs (as tuples)
#     """
#     return [pair for pair in
#             itertools.product([n for n in topology.nodes()], repeat=2)
#             if pair[0] != pair[1]]


# cpdef uniformTM(iepairs, double totalFlows):
#     """
#     Compute a uniform traffic matrix. That is each ingress-egress pair has the same number of flows
#
#     :param iepairs: list of ingress-egress tuples
#     :param totalFlows: total number of flows in the network
#     :return: the traffic matrix
#     """
#     return TrafficMatrix({ie: totalFlows / len(iepairs) for ie in iepairs})
#
#
# cpdef logNormalTM(iepairs, meanFlows):
#     """
#     Compute the log-normal distribution of traffic across ingress-egress pairs
#
#     :param iepairs: ingress-egress pairs
#     :param meanFlows: the average number of flows, around which the distribution is centered.
#     :return: the traffic matrix
#     """
#     dist = numpy.random.lognormal(0, .5)
#     return TrafficMatrix({ie: meanFlows * d for ie, d in six.zip(iepairs, dist)})
#
#
# cpdef gravityTM(iepairs, double totalFlows, populationDict):
#     """
#     Computes the gravity model traffic matrix base
#
#     :param iepairs: ingress-egress pairs
#     :param totalFlows: number of total flows in the network
#     :param populationDict: dictionary mapping nodeIDs to populations, which will be used to compute the model
#     :return: the traffic matrix as :py:class:`~sol.optimization.topology.traffic.TrafficMatrix`
#     """
#     tm = TrafficMatrix()
#     tot_population = sum(populationDict.values())
#
#     for i, e in iepairs:
#         ti_in = populationDict[i]
#         tj_out = populationDict[e]
#         tm[(i, e)] = ((float(ti_in * tj_out) / (tot_population ** 2)) * totalFlows)
#     return tm

cpdef traffic_classes(TrafficMatrix tm, dict fractions, dict class_bytes,
                      as_dict=False):
    """
    Generate traffic classes from a given traffic matrix

    :param tm: the traffic matrix object
    :param fractions: a dictionary mapping class name to a fraction of traffic.
        Must sum up to 1.
        Example::

            classFractionDict = {'web': .6, 'ssh': .2, 'voip': .2}

    :param class_bytes: dictionary mapping the class name to an average flow
        size in bytes.
        That is::

            classBytesDict = {'web': 100, 'ssh': 200, 'voip': 200}

        means that each web flow is 100 bytes, each ssh flow is 200 bytes and
        so on.
    :param as_dict: whether to return traffic classes as dictionary with keys
        being class names. If False, a flat list is returned

    .. warning:
        Assumes topology's nodes are contiguous and 0-indexed.
    """
    assert tm.matrix.shape[0] == tm.matrix.shape[1]
    assert sum(fractions.values()) == 1
    traffic_classes = []
    if as_dict:
        traffic_classes = {}
        for classname in iterkeys(fractions):
            traffic_classes[classname] = []
    cdef int index = 1, i = 0, j = 0
    cdef double fraction
    cdef np.ndarray volflows, volbytes
    for i in range(tm.matrix.shape[0]):
        for j in range(tm.matrix.shape[1]):
            if i != j:
                for classname, fraction in iteritems(fractions):
                    volflows = np.array([fraction * tm.between(i, j, 'mean')])
                    volbytes = volflows * class_bytes[classname]
                    # XXX: this assumes that topology nodes are 0-indexed
                    tc = TrafficClass(index, classname, i, j, volflows,
                                      volbytes)
                    if as_dict:
                        traffic_classes[classname].append(tc)
                    else:
                        traffic_classes.append(tc)
                    index += 1
    return traffic_classes

cdef compute_background_load(Topology topology, traffic_classes):
    """
    Compute the load on each link given the topology and traffic classes,
    assuming that all routing would be done using shortest-path routing.

    :param topology: The Topology object
    :param traffic_classes: list of traffic classes
    :return:
    """
    cdef int ind = 0
    paths = {}
    allsp = networkx.all_pairs_shortest_path(topology.get_graph())
    loads = {}
    cdef int u, v, i, e
    for u, v in topology.links():
        link = (u, v)
        loads[link] = 0
    for tc in traffic_classes:
        i, e = tc.iepair()
        path = allsp[i][e]
        for link in zip(path, path[1:]):
            load = tc.volBytes
            loads[link] += load
    return loads

cpdef provision_links(Topology topology, list traffic_classes,
                      float overprovision=3, bool set_attr=False):
    """ Provision the links in the topology based on the traffic classes.
    Computes shortest path routing for given traffic classes, uses the maximum
    load, scaled by *overprovision*, as the link capacity

    :param topology: topology of interest
    :param traffic_classes: list of traffic classes
    :param overprovision: the multiplier by which to overprovision the links
    :param set_attr: if True the topology graph will be modified to set
        the link *capacity* attribute for each link.
    :returns: mapping of links to their capacities
    :rtype: dict
    """

    bg = compute_background_load(topology, traffic_classes)
    cdef double max_bg = max(bg.values())
    capacities = {}
    cdef int u, v
    cdef double cap
    cdef int mult = 1
    for u, v, data in topology.links(True):
        link = (u, v)
        mult = 1
        if 'capacitymult' in data:
            mult = data['capacitymult']
        cap = overprovision * max_bg * mult
        if set_attr:
            topology.set_resource(link, BANDWIDTH, cap)
        capacities[link] = cap
    return capacities


# TODO: is this method even used?
# def compute_max_ingress_load(traffic_classes, tc_cost):
#     """
#     Compute the maximum load assuming all the processing would be done at
#     ingress nodes
#
#     :param traffic_classes: list of traffic classes
#     :param tc_cost: a mapping of traffic class to the processing cost (for a
#         particular resource)
#
#     :returns: max ingress load
#     """
#     loads = defaultdict(lambda: 0)
#     for tc in traffic_classes:
#         loads[tc.src] += (tc.volFlows * tc_cost[tc])
#     return float(max(loads.values()))
