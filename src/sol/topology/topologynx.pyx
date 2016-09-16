# coding=utf-8
"""
Implements the topology for SOL optimization
"""

import networkx as nx
from networkx.readwrite import graphml, json_graph

from cpython cimport bool
from sol.topology.varnames import _HAS_MBOX, _SWITCH, _SERVICES, _RESOURCES
from sol.utils.pythonHelper import parse_bool

# noinspection PyClassicStyleClass
cdef class Topology:
    """
    Class that stores the topology graph and provides helper functions
    (e.g., middlebox manipulation)

    """

    def __init__(self, str name, graph=None):
        """ Create a new empty topology

        :param name: The topology name
        :param graph: Either a

            #. :py:mod:`networkx` graph that represents the topology
            #. filename of a graphml file to load the graph from
            #. None, in which case an empty directed graph is created

        """
        self.name = name
        if graph is not None:
            if isinstance(graph, str):
                self.load_graph(graph)
            else:
                self._graph = graph
        else:
            self._graph = nx.DiGraph()
        self._process_graph()

    cdef _process_graph(self):
        """
        Initializes all the nodes to switches and sets resource dictionaries.
        """
        for n in self.nodes():
            self.add_service_type(n, _SWITCH)
        for n in self.nodes():
            if _RESOURCES not in self._graph.node[n]:
                self._graph.node[n][_RESOURCES] = {}
        for u, v in self.links():
            if _RESOURCES not in self._graph.edge[u][v]:
                self._graph.edge[u][v][_RESOURCES] = {}

    cpdef num_nodes(self, str service=None):
        """ Returns the number of nodes in this topology

        :param service: only count nodes that provide a particular service (
            e.g., 'switch', 'ids', 'fw', etc.)
        """
        if service is None:
            return self._graph.number_of_nodes()
        else:
            return len([n for n in self._graph.nodes_iter()
                        if 'services' in self._graph.node[n] and
                        service in self._graph.node[n]['services']])

    cpdef get_graph(self):
        """ Return the topology graph

        :return: :py:mod:`networkx` topology directed graph
        """
        return self._graph

    cpdef set_graph(self, graph):
        """ Set the graph

        :param graph: :py:mod:`networkx` directed graph
        """
        self._graph = graph

    def to_graphml(self, str fname):
        """
        Writes out the graph in GraphML format

        :param dir_name: directory to write to
        :param fname: file name to use. If None, topology name with a
            '.graphml' suffix is used
        """

    def write_graph(self, str fname, format='auto'):
        if format == 'auto':
            format = fname.split('.')[-1].lower()
        if format == 'graphml':
            graphml.write_graphml(self._graph, fname)
        elif format == 'gml':
            nx.write_gml(self._graph, fname)
        else:
            raise ValueError("Cannot find a supported format")

    def load_graph(self, str fname, format='auto'):
        if format == 'auto':
            format = fname.split('.')[-1].lower()
        if format == 'graphml':
            self._graph = graphml.read_graphml(fname, int).to_directed()
        elif format == 'gml':
            self._graph = nx.read_gml(fname)
        else:
            raise ValueError("Cannot find a supported format")

    cpdef get_service_types(self, int node):
        """
        Returns the list of services a particular node provides

        :param node: the node id of interest
        :return: a list of available services at this node (e.g., 'switch',
            'ids')
        """
        return self._graph.node[node][_SERVICES].split(';')

    cpdef set_service_types(self, int node, service_types):
        """
        Set the service types for this node

        :param node: the node id of interest
        :param service_types: a list of strings denoting the services
        :type service_types: list
        """
        if isinstance(service_types, str):
            self._graph.node[node][_SERVICES] = service_types
        else:
            self._graph.node[node][_SERVICES] = ';'.join(service_types)

    cpdef add_service_type(self, int node, service_type):
        """
        Add a single service type to the given node

        :param node: the node id of interest
        :param service_type: the service to add (e.g., 'switch', 'ids')
        :type service_type: str
        """
        if _SERVICES in self._graph.node[node]:
            types = set(self._graph.node[node][_SERVICES].split(';'))
            types.add(service_type)
        else:
            types = [service_type]
        self._graph.node[node][_SERVICES] = ';'.join(types)

    cpdef nodes(self, data=False):
        """
        Returns an iterator over the nodes in this topology

        :param data: whether to return the attributes associated with the node.
            If True, iterator will return elements of type (nodeID, attr_dict).
            If False, only nodeID will be returned
        """
        return self._graph.nodes_iter(data=data)

    cpdef edges(self, data=False):
        """
        Returns i
        :param data: whether to return the attributes associated with the edge
        :return: Iterator over topology edge tuples (nodeID1, nodeID2, edgeData)
        """
        return self._graph.edges_iter(data=data)

    cpdef links(self, data=False):
        """
        Another name for :py:meth:`edges`
        .. seealso::

            :py:meth:`edges`
        """
        return self.edges(data)

    cpdef set_resource(self, node_or_link, str resource, double capacity):
        """
        Set the given resources capacity on a node (or link)

        :param node_or_link: node (or link) for which resource capcity is being
            set
        :param resource: name of the resource
        :param capacity: resource capacity
        """
        if isinstance(node_or_link, tuple):
            assert len(node_or_link) == 2
            self._graph.edge[node_or_link[0]][node_or_link[1]][_RESOURCES][
                resource] = capacity
        else:
            self._graph.node[node_or_link][_RESOURCES][resource] = capacity

    cpdef dict get_resources(self, node_or_link):
        """
        Returns the resources (and their capacities) associated with given
        node or link
        :param node_or_link:
        :return:
        """
        if isinstance(node_or_link, tuple):
            assert len(node_or_link) == 2
            if _RESOURCES in self._graph.edge[node_or_link[0]][node_or_link[1]]:
                return self._graph.edge[node_or_link[0]][node_or_link[1]][
                    _RESOURCES]
            else:
                return {}
        else:
            if _RESOURCES in self._graph.node[node_or_link]:
                return self._graph.node[node_or_link][_RESOURCES]
            else:
                return {}

    def __repr__(self):
        return "{}(name={})".format(self.__class__, self.name)

    def copy(self):
        """
        Make a deep copy of this topology
        :return:
        """
        return Topology(self.name, self._graph.copy())

    def __copy__(self):
        return self.copy()

    cpdef bool has_middlebox(self, int node):
        """
        Check if the given node has a middlebox attached to it

        :param node: node ID to check
        :return: True or False
        """
        try:
            return parse_bool(self._graph.node[node][_HAS_MBOX])
        except KeyError:
            return False

    cpdef bool has_mbox(self, int node):
        return self.has_middlebox(node)

    cpdef set_middlebox(self, int node, val=True):
        """
        Indicate whether a middlebox is attached to a given node

        :param node: node ID
        :param val: True or False
        """
        self._graph.node[node][_HAS_MBOX] = str(val)

    cpdef set_mbox(self, int node, val=True):
        return self.set_middlebox(node, val)

    cpdef int diameter(self):
        return nx.diameter(self._graph)

    cpdef bool is_leaf(self, int node):
        return self._graph.node[node]['layer'] == 'edge'

    cpdef paths(self, int source, int sink, int cutoff):
        return nx.all_simple_paths(self._graph, source, sink, cutoff)

    def to_json(self):
        return json_graph.node_link_data(self._graph.to_undirected())
