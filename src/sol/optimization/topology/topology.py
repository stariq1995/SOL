# coding=utf-8
""" Implements the topology class

"""
from os.path import sep
import networkx as nx
from networkx.readwrite import graphml


class Topology(object):
    """
    Class that stores the topology graph as well as some traffic information,
    like number of flows in the network

    """

    def __init__(self, name, graph=None):
        """ Create a new empty topology

        :param name: The topology name
        :param graph: Either a
            1) :py:module:`networkx` graph that represents the topology
            2) filename of a graphml file to load the graph from

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

    def getNumNodes(self, service=None):
        """ Returns the number of nodes in this topology

        :param nodeType: only count nodes of particular nodeType (e.g., switch,
            host, middlebox)
        """
        if service is None:
            return self._graph.number_of_nodes()
        else:
            return len([n for n in self._graph.nodes_iter()
                        if 'services' in self._graph.node[n] and
                        service in self._graph.node[n]['services']])

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

    # def _istype(self, node, typ):
    # """
    # Check if given node is of a given type
    #
    #     :param node: node to check
    #     :param typ: type (e.g., middlebox, switch)
    #     :return: True or False
    #     """
    #     return 'functions' in self._graph.node[node] and \
    #            self._graph.node[node]['functions'].lower() == typ.lower()
    #
    # def isMiddlebox(self, node):
    #     """ Check if given node is a middlebox
    #
    #     :param node: node to check
    #     :return: True or False
    #     """
    #     return self._istype(node, 'middlebox')
    #
    # def isSwitch(self, node):
    #     """ Check if given node is a switch
    #
    #     :param node: node to check
    #     :return: True or False
    #     """
    #     return self._istype(node, 'switch')

    def __repr__(self):
        return "{}(name={})".format(self.__class__, self.name)




