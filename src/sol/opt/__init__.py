# coding=utf-8
from itertools import chain

from sol.utils import Tree
from sol.utils.const import ERR_NO_RESOURCE, ERR_BAD_CAPVAL, Fairness


class NetworkCaps(object):
    """
        Represents caps of resources assigned to nodes/links.
        The optimization will respect these caps.
        .. note::
            This is different from **capacities** which are absolute quantities of
            resources assigned to link/nodes.

            Caps are relative loads allowed on those resources and must be between 0 and 1.
    """

    def __init__(self, topology):
        """
        Create a new caps object.
        :param topology: The topology over which the optimization will be done.
            This allows us to keep track of existing nodes, links and resources.
        """
        self._caps = Tree()
        self._topo = topology
        self._resources = set()

    def add_cap(self, resource, node_or_link=None, cap=None):
        """
        Add a cap for a given resource to a given node (or link)

        :param resource: the resource to cap
        :param node_or_link: node or link. If None, all nodes/links with the given resource are capped.
        :param cap: cap value. Must be between 0 and 1.
        """
        if cap is None:
            cap = 1
        if cap < 0 or cap > 1:
            raise ValueError(ERR_BAD_CAPVAL)
        if node_or_link is None:
            # get all the nodes and link which have given resource
            # and set the cap
            for n in chain(self._topo.nodes(), self._topo.links()):
                if resource in self._topo.get_resources(n):
                    self._caps[n][resource] = cap
        else:
            if resource not in self._topo.get_resources(node_or_link):
                raise ValueError(ERR_NO_RESOURCE % (node_or_link, resource))
            self._caps[node_or_link][resource] = cap
        self._resources.add(resource)

    def capval(self, resource, node_or_link):
        """
        Get the cap value for given resource and node (or link).
        :param resource: the resource
        :param node_or_link: node or link which we are capping
        :rtype: float
        """
        return self._caps[node_or_link][resource]

    def caps(self, resource):
        """
        Get a dictionary containing a mapping from nodes (and links) to caps for a given resource.
        Missing nodes or links indicate no cap has been set.

        :param resource:
        :return:
        """
        return {n: self._caps[n][resource] for n in self._caps if resource in self._caps[n]}

    def resources(self):
        """
        Return a set of all resources that are capped.
        """
        return self._resources

    def __repr__(self):
        return "NetworkCaps: {}".format(self._caps)



class NetworkConfig(object):
    """
    Represents the network configuration to be used when constructing the optimization.
    Specified by the "owner" of the network and contains things like resource caps,
    application composition mode, etc.

    .. note ::
        Number of supported configurations could be extended in the future without
        backwards compatibility.
    """

    def __init__(self, networkcaps=None):
        self.networkcaps = networkcaps
        # self.compose_mode = compose_mode

    def get_caps(self):
        """
        Get the optimization network caps
        :return: all of the network caps for given network
        :rtype: :py:class:NetworkCaps
        """
        return self.networkcaps
