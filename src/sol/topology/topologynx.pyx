# coding=utf-8
"""
Implements the topology for SOL optimization
"""
import networkx as nx
from networkx.readwrite import graphml, json_graph

from cpython cimport bool
from sol.topology.generators import EDGE_LAYER
from sol.utils.const import FORMAT_AUTO, FORMAT_GRAPHML, FORMAT_GML, SERVICES, \
    SWITCH, RESOURCES, HAS_MBOX, ERR_FMT
from sol.utils.ph import parse_bool


# noinspection PyClassicStyleClass
cdef class Topology:
    """
    Stores network topology graph
    """

    def __init__(self, unicode name, graph=None):
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
            self.add_service_type(n, SWITCH)
        for n in self.nodes():
            if RESOURCES not in self._graph.node[n]:
                self._graph.node[n][RESOURCES] = {}
        for u, v in self.links():
            if RESOURCES not in self._graph.edge[u][v]:
                self._graph.edge[u][v][RESOURCES] = {}

    cpdef num_nodes(self, unicode service=None):
        """ Returns the number of nodes in this topology

        :param service: only count nodes that provide a particular service (
            e.g., 'switch', 'ids', 'fw', etc.)
        """
        if service is None:
            return self._graph.number_of_nodes()
        else:
            return len([n for n in self._graph.nodes_iter()
                        if SERVICES in self._graph.node[n] and
                        service in self._graph.node[n][SERVICES]])

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

    def write_graph(self, unicode fname, fmt='auto'):
        """ Save the topology to disk
        :param fname: the filename
        :param fmt: format either 'auto' for autodetection based on extension,
            'graphml' or 'gml'
        """
        if fmt == FORMAT_AUTO:
            fmt = fname.split('.')[-1].lower()
        if fmt == FORMAT_GRAPHML:
            graphml.write_graphml(self._graph, fname)
        elif fmt == FORMAT_GML:
            nx.write_gml(self._graph, fname)
        else:
            raise ValueError(ERR_FMT)

    def load_graph(self, unicode fname, fmt='auto'):
        """
        Load topology from disk
        :param fname: filename
        :param fmt: format either 'auto' for autodetection based on extension,
            'graphml' or 'gml'
        """
        if fmt == FORMAT_AUTO:
            fmt = fname.split('.')[-1].lower()
        if fmt == FORMAT_GRAPHML:
            self._graph = graphml.read_graphml(fname, int).to_directed()
        elif fmt == FORMAT_GML:
            self._graph = nx.read_gml(fname)
        else:
            raise ValueError(ERR_FMT)

    cpdef get_service_types(self, int node):
        """
        Returns the list of services a particular node provides

        :param node: the node id of interest
        :return: a list of available services at this node (e.g., 'switch',
            'ids')
        """
        return self._graph.node[node][SERVICES].split(';')

    cpdef set_service_types(self, int node, service_types):
        """
        Set the service types for this node

        :param node: the node id of interest
        :param service_types: a list of strings denoting the services
        :type service_types: list
        """
        if isinstance(service_types, str):
            self._graph.node[node][SERVICES] = service_types
        else:
            self._graph.node[node][SERVICES] = u';'.join(service_types)

    cpdef add_service_type(self, int node, service_type):
        """
        Add a single service type to the given node

        :param node: the node id of interest
        :param service_type: the service to add (e.g., 'switch', 'ids')
        :type service_type: str
        """
        if SERVICES in self._graph.node[node]:
            types = set(self._graph.node[node][SERVICES].split(';'))
            types.add(service_type)
        else:
            types = [service_type]
        self._graph.node[node][SERVICES] = u';'.join(types)

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

    cpdef set_resource(self, node_or_link, unicode resource, double capacity):
        """
        Set the given resources capacity on a node (or link)

        :param node_or_link: node (or link) for which resource capcity is being
            set
        :param resource: name of the resource
        :param capacity: resource capacity
        """
        if isinstance(node_or_link, tuple):
            assert len(node_or_link) == 2
            self._graph.edge[node_or_link[0]][node_or_link[1]][RESOURCES][
                resource] = capacity
        else:
            self._graph.node[node_or_link][RESOURCES][resource] = capacity

    cpdef dict get_resources(self, node_or_link):
        """
        Returns the resources (and their capacities) associated with given
        node or link
        :param node_or_link:
        :return:
        """
        if isinstance(node_or_link, tuple):
            assert len(node_or_link) == 2
            if RESOURCES in self._graph.edge[node_or_link[0]][node_or_link[1]]:
                return self._graph.edge[node_or_link[0]][node_or_link[1]][
                    RESOURCES]
            else:
                return {}
        else:
            if RESOURCES in self._graph.node[node_or_link]:
                return self._graph.node[node_or_link][RESOURCES]
            else:
                return {}

    def __repr__(self):
        return u"{}(name={})".format(self.__class__, self.name)

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
            return parse_bool(self._graph.node[node][HAS_MBOX])
        except KeyError:
            return False

    cpdef bool has_mbox(self, int node):
        """ Alias for has_middlebox """
        return self.has_middlebox(node)

    cpdef set_middlebox(self, int node, val=True):
        """
        Set whether a middlebox is attached to a given node

        :param node: node ID
        :param val: True or False
        """
        self._graph.node[node][HAS_MBOX] = str(val)

    cpdef set_mbox(self, int node, val=True):
        return self.set_middlebox(node, val)

    cpdef int diameter(self):
        return nx.diameter(self._graph)

    cpdef bool is_leaf(self, int node):
        return self._graph.node[node][u'layer'] == EDGE_LAYER

    cpdef paths(self, int source, int sink, int cutoff):
        return nx.all_simple_paths(self._graph, source, sink, cutoff)

    def to_json(self):
        return json_graph.node_link_data(self._graph.to_undirected())
