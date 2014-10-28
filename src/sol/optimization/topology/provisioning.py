# coding=utf-8
from collections import defaultdict
import itertools
import networkx
import numpy

from sol.optimization.topology.traffic import TrafficClass, TrafficMatrix, Path


def generateIEpairs(topology):
    return [pair for pair in
            itertools.product([n for n, d in topology.nodes()], repeat=2)
            if pair[0] != pair[1]]


def computeUniformTrafficMatrixPerIE(iepairs, totalFlows):
    return TrafficMatrix({ie: totalFlows / len(iepairs) for ie in iepairs})


def computeUnifromPlusNormalODTM(iepairs, totalFlows, std=.5):
    tm = dict()
    uniform = totalFlows / len(iepairs)
    vals = numpy.random.normal(uniform, scale=std*uniform, size=len(iepairs))
    vals = numpy.clip(vals, std * uniform, (1 + std) * uniform)
    for index, ie in enumerate(iepairs):
        tm[ie] = vals[index]
    return TrafficMatrix(tm)


def computeGravityTrafficMatrixPerIE(iepairs, totalFlows, populationDict):
    raise NotImplementedError()


def computeDirichletTrafficMatrixPerIE(iepairs, totalFlows):
    raise NotImplementedError()

# todo: implement other types of traffic matrices


def generateTrafficClasses(iepairs, trafficMatrix, classFractionDict,
                           classBytesDict):
    trafficClasses = []
    index = 1
    for ie in iepairs:
        i, e = ie
        for classname, fraction in classFractionDict.iteritems():
            volflows = fraction * trafficMatrix[ie]
            volbytes = volflows * classBytesDict[classname]
            trafficClasses.append(TrafficClass(index, classname, i, e, volflows,
                                               volbytes))
            index += 1
    return trafficClasses


def provisionLinks(topology, trafficClasses, overprovision=3,
                   setAttr=True):
    """ Provision the links in the topology based on the traffic classes.
    Computes shortest path routing for given traffic classes, uses the maximum
    load, scaled by *overprovision*, as the link capacity

    :param topology: topology of interest
    :param trafficClasses: list of traffic classes
    :param overprovision: the multiplier by which to overprovision the links
    :param setAttr: if True the topology graph will be modified to set
        the link *capacity* attribute for each link.
    :returns: mapping of links to their capacities
    :rtype: dict
    """

    def computeBackgroundLoad(topology, trafficClasses):

        paths = {}
        allsp = networkx.all_pairs_shortest_path(topology.getGraph())
        for tc in trafficClasses:
            i, e = tc.getIEPair()
            paths[(i, e)] = Path(allsp[i][e])
        loads = {}
        for link in topology.links():
            loads[link] = 0
        for tc in trafficClasses:
            path = paths[tc.getIEPair()]
            for link in path.getLinks():
                l = tc.volBytes
                loads[link] += l
        return loads

    bg = computeBackgroundLoad(topology, trafficClasses)
    maxBackground = max(bg.itervalues())
    capacities = {}
    G = topology.getGraph()
    for link in topology.links():
        u, v = link
        mult = 1
        if 'capacitymult' in G.edge[u][v]:
            mult = G.edge[u][v]['capacitymult']
        capacities[link] = float(overprovision * maxBackground * mult)

        if setAttr:
            G.edge[u][v]['capacity'] = capacities[link]
    return capacities


def computeMaxIngressLoad(trafficClasses, tcCost):
    """
    Compute the maximum load assuming all the processing would be done at
    ingress nodes

    :param trafficClasses: list of traffic classes
    :param tcCost: a mapping of traffic class to the processing cost (for a
        particular resource)

    :returns: max ingress load
    """

    loads = defaultdict(lambda: 0)
    for tc in trafficClasses:
        loads[tc.src] += (tc.volFlows * tcCost[tc])
    return float(max(loads.values()))
