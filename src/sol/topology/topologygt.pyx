# coding=utf-8
# coding=utf-8
""" Implements the topology for SOL optimization

"""

from os.path import sep
from graph_tool.all import Graph, load_graph

from cpython cimport bool

from sol.topology.varnames import _HAS_MBOX, _SWITCH, _SERVICES, _RESOURCES

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
            #) :py:mod:`networkx` graph that represents the topology
            #) filename of a graphml file to load the graph from
            #) None, in which case an empty directed graph is created

        """
        self.name = name
        if graph is not None:
            if isinstance(graph, str):
                self.load_graph(graph)
            else:
                self._graph = graph
        else:
            self._graph = Graph()
        # self._process_graph()

    # cdef _process_graph(self):
    #     """
    #     Initializes all the nodes to switches and sets resource dictionaries.
    #     """
    #     ## FIXME
    #     self._services = self._graph.new_vertex_property('vector<string>',
    #                                                      val=[_SWITCH])
    #     self._node_resources = self._graph.new_vertex_property('python::object')
    #     self._link_resources = self._graph.new_vertex_property('python::object')
    #     self._middleboxes = self._graph.new_vertex_property('bool')
    #     for n in self.nodes():
    #         self.add_service_type(n, _SWITCH)
    #     for n in self.nodes():
    #         if _RESOURCES not in self._graph.node[n]:
    #             self._graph.node[n][_RESOURCES] = {}
    #     for u, v in self.links():
    #         if _RESOURCES not in self._graph.edge[u][v]:
    #             self._graph.edge[u][v][_RESOURCES] = {}

    cpdef int num_nodes(self, str service=None):
        """ Returns the number of nodes in this topology

        :param service: only count nodes that provide a particular service (
            e.g., 'switch', 'ids', 'fw', etc.)
        """
        # FIXME
        cdef int n = 0
        if service is None:
            return self._graph.num_vertices(ignore_filters=True)
        else:
            raise NotImplemented

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

    def write_graph(self, str dir_name, str fname=None):
        n = self.name + '.graphml' if fname is None else fname
        self._graph.save(dir_name + sep + n)

    def load_graph(self, str fname):
        self._graph = load_graph(fname, int).set_directed()

    # cpdef get_service_types(self, node):
    #     """
    #     Returns the list of services a particular node provides
    #
    #     :param node: the node id of interest
    #     :return: a list of available services at this node (e.g., 'switch',
    #         'ids')
    #     """
    #     # FIXME
    #     return self._graph.node[node][_SERVICES].split(';')
    #
    # cpdef set_service_types(self, node, service_types):
    #     """
    #     Set the service types for this node
    #
    #     :param node: the node id of interest
    #     :param service_types: a list of strings denoting the services
    #     :type service_types: list
    #     """
    #     # FIXME
    #     if isinstance(service_types, str):
    #         self._graph.node[node][_SERVICES] = service_types
    #     else:
    #         self._graph.node[node][_SERVICES] = ';'.join(service_types)

    # cpdef add_service_type(self, node, service_type):
    #     """
    #     Add a single service type to the given node
    #
    #     :param node: the node id of interest
    #     :param service_type: the service to add (e.g., 'switch', 'ids')
    #     :type service_type: str
    #     """
    #     # FIXME
    #     if _SERVICES in self._graph.node[node]:
    #         types = set(self._graph.node[node][_SERVICES].split(';'))
    #         types.add(service_type)
    #     else:
    #         types = [service_type]
    #     self._graph.node[node][_SERVICES] = ';'.join(types)

    cpdef nodes(self, data=False):
        """
        :param data: whether to return the attributes associated with the node
        :return: Iterator over topology nodes as tuples of the form (nodeID, nodeData)
        """
        # FIXME: support data
        return self._graph.vertices()

    cpdef edges(self, data=False):
        """
        :param data: whether to return the attributes associated with the edge
        :return: Iterator over topology edge tuples (nodeID1, nodeID2, edgeData)
        """
        # FIXME: support data
        return self._graph.edges()

    cpdef links(self, data=False):
        """
        Alias to edges
        """
        return self.edges(data)

    # cpdef set_resource(self, node_or_link, str resource, double capacity):
    #     """
    #     Set the given resources capacity on a node (or link)
    #     :param node_or_link: node (or link) for which resource capcity is being
    #         set
    #     :param resource: name of the resource
    #     :param capacity: resource capacity
    #     """
    #     # FIXME
    #     if isinstance(node_or_link, tuple):
    #         assert len(node_or_link) == 2
    #         self._graph.edge[node_or_link[0]][node_or_link[1]][_RESOURCES][
    #             resource] = capacity
    #     else:
    #         self._graph.node[node_or_link][_RESOURCES][resource] = capacity
    #
    # cpdef dict get_resources(self, node_or_link):
    #     """
    #     Returns the resources (and their capacities) associated with given
    #     node or link
    #     :param node_or_link:
    #     :return:
    #     """
    #     # FIXME
    #     if isinstance(node_or_link, tuple):
    #         assert len(node_or_link) == 2
    #         if _RESOURCES in self._graph.edge[node_or_link[0]][node_or_link[1]]:
    #             return self._graph.edge[node_or_link[0]][node_or_link[1]][
    #                 _RESOURCES]
    #         else:
    #             return {}
    #     else:
    #         if _RESOURCES in self._graph.node[node_or_link]:
    #             return self._graph.node[node_or_link][_RESOURCES]
    #         else:
    #             return {}

    def __repr__(self):
        return "{}(name={})".format(self.__class__, self.name)

    def copy(self):
        """
        Make a deep copy of this topology
        :return:
        """
        return Topology(self.name, Graph(self._graph))

    def __copy__(self):
        return self.copy()

    # cpdef bool has_middlebox(self, node):
    #     """
    #     Check if the given node has a middlebox attached to it
    #
    #     :param node: node ID to check
    #     :return: True or False
    #     """
    #     # FIXME
    #     try:
    #         return self._graph.node[node][_HAS_MBOX]
    #     except KeyError:
    #         return False
    #
    # cpdef bool has_mbox(self, node):
    #     return self.has_middlebox(node)
    #
    # cpdef set_middlebox(self, node, val=True):
    #     # FIXME
    #     """
    #     Indicate whether a middlebox is attached to a given node
    #
    #     :param node: node ID
    #     :param val: True or False
    #     """
    #     self._graph.node[node][_HAS_MBOX] = val
    #
    # cpdef set_mbox(self, node, val=True):
    #     return self.set_middlebox(node, val)
