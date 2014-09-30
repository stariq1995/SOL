""" Implements the topology classes

..note::
    The topology classes have many methods of the form topology.generate*()
    which help in the evaluation of this project. They are defaults that seemed
    appropriate at the time, but there are many other ways to implement them
    depending on the desired application

"""
import abc
import itertools
from os.path import sep
from collections import defaultdict

import networkx as nx
from networkx.readwrite import graphml
import numpy

from traffic import TrafficMatrix, Commodity, Path


class Topology(object):
    """
    Class that stores the topology graph as well as some traffic information,
    like number of flows and traffic volume across the network

    For the purposes of the given framework, we keep two versions of the
    topology: the "original" topology (just the switches)

    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, graph=None, numFlows=0):
        """ Create a new empty topology

        :param name: The topology name
        :param graph: a :py:module:`networkx` graph that represents the topology
        :param numFlows: number of flows in the network

        """
        self.name = name
        if graph is not None:
            if isinstance(graph, str):
                self.loadGraph(graph)
            else:
                self._graph = graph
        else:
            self._graph = nx.DiGraph()
        self._numFlows = numFlows

    def getNumFlows(self):
        """Returns the number of flows in this network"""
        return self._numFlows

    def setNumFlows(self, numFlows):
        """ Sets the number of flows across this network
        :param numFlows: the new number of flows in the network
        """
        self._numFlows = numFlows
        self._graph.graph['numFlows'] = numFlows

    def getNumNodes(self, nodeType=None):
        """ Returns the number of nodes in this topology

        :param nodeType: only count nodes of particular nodeType (e.g., switch,
            host, middlebox)
        """
        if nodeType is None:
            return self._graph.number_of_nodes()
        else:
            return len([n for n in self._graph.nodes_iter()
                        if 'functions' in self._graph.node[n] and \
                        self._graph.node[n]['functions'] == nodeType])

    def getGraph(self):
        """ Return the topology graph

        :returns :py:mod:`networkx` topology directed graph
        """
        return self._graph

    def setGraph(self, graph):
        """ Set the graph

        :param graph: :py:mod:`networkx` directed graph
        """
        self._graph = graph


    def writeGraph(self, dirName, fname=None):
        """
        Writes out the graph in GraphML format

        :param dirName: directory to write to
        :param fname: file name to use. If None, topology name is used
        """
        n = self.name + '.graphml' if fname is None else fname
        graphml.write_graphml(
            self._graph, dirName + sep + n)


    def loadGraph(self, fName):
        """ Loads the topology graph from a file in GraphML format

        :param fName: the name of the file to read from
        """
        self._graph = graphml.read_graphml(fName, int)
        self._numFlows = self._graph.graph['numFlows']

    def _istype(self, node, typ):
        """
        Check if given node is of a given type

        :param node: node to check
        :param typ: type (e.g., middlebox, switch)
        :return: True or False
        """
        return 'functions' in self._graph.node[node] and \
               self._graph.node[node]['functions'].lower() == typ.lower()

    def isMiddlebox(self, node):
        """ Check if given node is a middlebox

        :param node: node to check
        :return: True or False
        """
        return self._istype(node, 'middlebox')

    def isSwitch(self, node):
        """ Check if given node is a switch

        :param node: node to check
        :return: True or False
        """
        return self._istype(node, 'switch')

    def isSink(self, node):
        """ Check if given node is a sink
        :param node: node to check
        :return: True or False
        """
        return 'superSink' in self._graph.node[node]

    def __repr__(self):
        return "{}(name={})".format(self.__class__, self.name)

    @abc.abstractmethod
    def generateIEPairs(self):
        """
        Generates the ingress egress pairs
        """
        return

    @abc.abstractmethod
    def generateTrafficMatrix(self, nodePairs, model):
        """ Generates the traffic matrix
        :param nodePairs: use the following IE pairs
        :param model: traffic model
        :return:
        """
        return

    @staticmethod
    def generateCommodities(nodePairs, trafficMatrix, trafficClasses):
        """ Generate the commodities for given node pairs, traffic matrix and
        traffic classes

        :param nodePairs: Node pairs that define commodities
        :param trafficMatrix: traffic matrix class
            (see :py:class:`~panacea.optimization.topology.traffic.TrafficMatrix`)
        :param trafficClasses: a list of traffic class objects
        Returns a list of Commodity objects
        """
        commodities = []
        index = 0
        for s, t in nodePairs:
            for cl in trafficClasses:
                vol = trafficMatrix.getODMatrix()[(s, t)] * \
                      cl.fraction
                commodities.append(Commodity(index, s, t, cl, vol))
                index += 1
        return commodities

    @staticmethod
    def setPathsPerCommodity(iepaths, commodities):
        """
        Generates paths per commodity based on the paths per IE pair and the
        commodities.

        :param iepaths: dictionary of (src, dst) tuples to the list of paths
        :param commodities: a list of commodities
        :return: paths per commodity
        :rtype: dict
        :raises KeyError: if iepaths do not match all commodities
        """
        result = {}
        for k in commodities:
            result[k] = iepaths[(k.src, k.dst)]
        return result

    def computeUniformODTM(self, nodePairs):
        """ Computes the uniform traffic matrix for this topology

        :param nodePairs: the ingress-egress pairs between which traffic \
        should be flowing.
        :returns: the traffic matrix object containing the OD traffic matrix
        """
        tm = dict()
        for i, e in nodePairs:
            tm[(i, e)] = self.getNumFlows() / len(nodePairs)
        return TrafficMatrix(tm)

    def computeDirichletODTM(self, nodePairs):
        tm = dict()
        vals = numpy.random.dirichlet(numpy.ones(len(nodePairs)))
        print vals
        print sum(vals)
        for (index, (i, e)) in enumerate(nodePairs):
            tm[(i, e)] = self.getNumFlows() * vals[index]
        return TrafficMatrix(tm)

    def computeUnifromPlusNormalODTM(self, nodePairs, std=.5):
        tm = dict()
        uni = self.getNumFlows() / len(nodePairs)
        vals = numpy.random.normal(uni, scale=std*uni, size=len(nodePairs))
        vals = numpy.clip(vals, std*uni, (1+std)*uni)
        for index,ie in enumerate(nodePairs):
            tm[ie] = vals[index]
        return TrafficMatrix(tm)


    def calculateBackgroundLoad(self, trafficMatrix, trafficClasses,
                                setAttr=True):
        """
        Calculate background load on all links under given traffic load
        Useful for provisioning links

        :param trafficMatrix: traffic matrix to use. If a perPath matrix is
            present, it will be used, otherwise shortest path routing will be
            computed for the perOD matrix
        :param trafficClasses: list of traffic classes
        :param setAttr: set the calculated link loads as the *'backgroundLoad'*
            attribute in the graph
        :returns: a dictionary of links to background loads
        :rtype: dict
        """
        pathTM = trafficMatrix.getPathMatrix()
        if pathTM is None:
            paths = []
            allsp = nx.all_pairs_shortest_path(self._graph)
            for i, e in trafficMatrix.getODPairs():
                paths.append(Path(allsp[i][e]))
            pathTM = trafficMatrix.convertODtoPathMatrix(paths)

        loads = {}
        for link in self._graph.edges_iter():
            loads[link] = 0
        for path in pathTM:
            pathedges = itertools.izip(path.getNodes()[0:],
                                       path.getNodes()[1:])
            for link in pathedges:
                for cl in trafficClasses:
                    l = path.getNumFlows() * cl.avgSize * cl.fraction
                    loads[link] += l
        if setAttr:
            for l in loads:
                u, v = l
                self._graph.edge[u][v]['backgroundLoad'] = loads[l]
        return loads

    def provisionLinks(self, trafficMatrix, trafficClasses, overprovision=3,
                       setAttr=True):
        """ Provision the links in the topology based on the traffic matrix
        and the traffic classes.

        :param trafficMatrix: the traffic matrix to use
        :param trafficClasses: list of traffic classes
        :param overprovision: the multiplier by which we scale the maximum
            computed background load
        :param setAttr: if True the topology graph will be modified to set
            the link *capacity* attribute for each link.
        :returns: mapping of links to their capacities
        :rtype: dict
        """
        bg = self.calculateBackgroundLoad(trafficMatrix, trafficClasses,
                                          setAttr=False)
        maxBackground = max(bg.itervalues())
        capacities = {}
        for link in self._graph.edges():
            u, v = link
            mult = 1
            if 'capacitymult' in self._graph.edge[u][v]:
                mult = self._graph.edge[u][v]['capacitymult']
            capacities[link] = float(overprovision * maxBackground * mult)

            if setAttr:
                self._graph.edge[u][v]['capacity'] = capacities[link]
        return capacities

    def provisionNodes(self, trafficMatrix, trafficClasses, resources,
                       setAttr=True, nodeTypes=None, overprovision=2):
        """ Calculate the node capacity for given resources.
        This is done by assuming all processing is done at ingress.

        :param trafficMatrix: traffic matrix to use
        :param trafficClasses: list of traffic classes
        :param resources: resources for which we are computing
        :param setAttr: whether we should set the node capacity attributes in
            the  graph
        :param nodeTypes: types of nodes for which *setAttr* applies.
            Default is *middlebox*
        :returns: mapping between a resource and max node capacity
        :rtype: dict
        """
        if not nodeTypes: nodeTypes = ['middlebox']
        tm = trafficMatrix.getODMatrix()
        capacities = {}
        for r in resources:
            loads = defaultdict(lambda: 0)
            for ie in tm.iterkeys():
                i, e = ie
                for cl in trafficClasses:
                    loads[i] += (tm[ie] * cl['{}cost'.format(r)] *
                                 cl.fraction)
            maxLoad = float(max(loads.values()) * overprovision)
            print type(maxLoad)
            if setAttr:
                G = self._graph
                for node in G.nodes():
                    if 'functions' in G.node[node] and G.node[node][ \
                            'functions'] in nodeTypes:
                        G.node[node]['{}capacity'.format(r)] = maxLoad
            capacities[r] = maxLoad
        return capacities



