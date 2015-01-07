# coding=utf-8
from collections import defaultdict

import networkx
import numpy

import itertools
from sol.optimization.topology.traffic import TrafficClass, TrafficMatrix, Path
from sol.utils.pythonHelper import deprecated


def generateIEpairs(topology):
    """
    Default way of generating ingress-egress pairs. Generates all possible n*(n-1) node combinations

    :param topology: the topology to work with
    :type topology: sol.optimization.topology.Topology
    :return: list of ingress-egress pairs (as tuples)
    """
    return [pair for pair in
            itertools.product([n for n, d in topology.nodes()], repeat=2)
            if pair[0] != pair[1]]


def computeUniformTrafficMatrixPerIE(iepairs, totalFlows):
    """
    Compute a uniform traffic matrix. That is each ingress-egress pair has the same number of flows

    :param iepairs: list of ingress-egress tuples
    :param totalFlows: total number of flows in the network
    :return: the traffic matrix
    """
    return TrafficMatrix({ie: totalFlows / len(iepairs) for ie in iepairs})


def computeLogNormalTrafficMatrixPerIE(iepairs, meanFlows):
    """
    Compute the log-normal distribution of traffic across ingress-egress pairs

    :param iepairs: ingress-egress pairs
    :param meanFlows: the average number of flows, around which the distribution is centered.
    :return: the traffic matrix
    """
    dist = numpy.random.lognormal(0, .5)
    return TrafficMatrix({ie: meanFlows * d for ie, d in itertools.izip(iepairs, dist)})


@deprecated
def computeUnifromPlusNormalODTM(iepairs, totalFlows, std=.5):
    """
    .. warning::
        deprecated

    A so-so way of generating the traffic matrix.
    Draw from a normal distribution centered around the uniform-mean.
    (That is, the mean is what uniform traffic matrix would be like)
    Then, values that fall outside of the standard deviation are clipped.

    :param iepairs: ingress-egress pairs
    :param totalFlows: total number of flow desired (only used to compute the uniform mean)
    :param std: standrard deviation of the normal distribution (as a fraction)
    :return: the new traffic matrix
    """
    tm = dict()
    uniform = totalFlows / len(iepairs)
    vals = numpy.random.normal(uniform, scale=std * uniform, size=len(iepairs))
    vals = numpy.clip(vals, std * uniform, (1 + std) * uniform)
    for index, ie in enumerate(iepairs):
        tm[ie] = vals[index]
    return TrafficMatrix(tm)


def computeGravityTrafficMatrixPerIE(iepairs, totalFlows, populationDict):
    """
    Computes the gravity model traffic matrix base

    :param iepairs: ingress-egress pairs
    :param totalFlows: number of total flows in the network
    :param populationDict: dictionary mapping nodeIDs to populations, which will be used to compute the model
    :return: the traffic matrix as :py:class:`~sol.optimization.topology.traffic.TrafficMatrix`
    """
    tm = TrafficMatrix()
    tot_population = sum(populationDict.values())

    for i, e in iepairs:
        ti_in = populationDict[i]
        tj_out = populationDict[e]
        tm[(i, e)] = ((float(ti_in * tj_out) / (tot_population ** 2)) * totalFlows)
    return tm


def generateTrafficClasses(iepairs, trafficMatrix, classFractionDict,
                           classBytesDict):
    """
    Generate traffic classes from given ingress-egress pairs and traffic matrix

    :param iepairs: list of ingress-egress pairs (as tuples)
    :param trafficMatrix: the traffic matrix object
    :param classFractionDict: a dictionary mapping class name to a fraction of traffic (in flows).
        Must sum up to 1.
        Example::

            classFractionDict = {'web': .6, 'ssh': .2, 'voip': .2}

        .. note::

            This does assume that the split is even across all ingress-egress pairs

    :param classBytesDict: dictionary mapping class name to an average flow size in bytes.
        That is::

            classBytesDict = {'web': 100, 'ssh': 200, 'voip': 200}

        means that each web flow is 100 bytes, each ssh flow is 200 bytes and so on.
    :return: a list of traffic classes
    """
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
        for u, v, data in topology.links():
            link = (u, v)
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
    for u, v, data in topology.links():
        link = (u, v)
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
