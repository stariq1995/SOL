from sol.topology.resource import Resource, CompoundResource


class Path(object):
    """ Represents a path in the network"""

    def __init__(self, nodes, numFlows=0):
        """Create a new path

        :param nodes: a list of node ids that belong to a path
        :param numFlows: the number of flows on this path
        """
        self._nodes = list(nodes)
        self._numFlows = numFlows
        self._computeLinks()

    @staticmethod
    def decode(dictionary):
        """
        Create a new path from a dict
        :param dictionary: dict type, must contain following keys:

            'nodes': maps to a list of nodes
        """
        return Path(dictionary['nodes'], dictionary.get('numFlows', 0))

    def _computeLinks(self):
        self._links = tuple(zip(self._nodes, self._nodes[1:]))

    def getIngress(self):
        """
        :return: the ingress node of this path
        """
        return self._nodes[0]

    def getEgress(self):
        """
        :return: the egress node of this path
        """
        return self._nodes[-1]

    def getNodes(self):
        """
        :return: all nodes as a list
        """
        return self._nodes

    def getNodesAsTuple(self):
        """
        :return: all nodes in this path as a tuple
        """
        return tuple(self._nodes)

    def getIEPair(self):
        """
        :return: ingress-egress pair for this path
        :rtype: tuple
        """
        return self.getIngress(), self.getEgress()

    def getNumFlows(self):
        """
        :return: the number of flows on this path.
        """
        return self._numFlows

    def setNumFlows(self, nflows):
        """
        Set number of flows on this path

        :param nflows: the new number of flows
        """
        self._numFlows = nflows

    def getLinks(self):
        """
        :return: Return an iterator over the links in this path
        """
        return zip(self._nodes, self._nodes[1:])
        # return self._links


    def encode(self):
        """
        Encode this path in dict/list form so it can be JSON-ed or MsgPack-ed

        :return: dictionary representation of this path
        """
        return {'nodes': self._nodes, 'numFlows': self._numFlows, 'Path':True}

    def __contains__(self, obj):
        if isinstance(obj, Resource):
            _hasResource(self, obj)
        elif isinstance(obj, CompoundResource):
            _hasCompoundResource(self, obj)
        else:
            return obj in self._nodes

    def _hasResource(self, res):
        #TODO:
        for node in nodes:
        raise NotImplemented

    def _hasCompoundResource(self, res):
        # TODO:
        raise NotImplemented

    def __delitem__(self, index):
        del self._nodes[index]

    def __setitem__(self, index, val):
        self._nodes[index] = val

    def __iter__(self):
        return self._nodes.__iter__()

    def __len__(self):
        return len(self._nodes)

    def __repr__(self):
        return "Path(nodes={}, numFlows={})".format(str(self._nodes),
                                                    self._numFlows)

    # def __key(self):
    #     return tuple(self._nodes)

    def __eq__(self, other):
        if isinstance(other, Path):
            return self._nodes == other._nodes
        else:
            return False

    # This breaks hashing things. why?
    # def __hash__(self):
    #     return hash(self.__key())

    def __getitem__(self, i):
        return self._nodes[i]


class PathWithMbox(Path):
    """
    Create a new path with middlebox

    :param nodes: path nodes (an ordered list)
    :param useMBoxes: at which nodes the middleboxes will be used
    :param numFlows: number of flows (if any) along this path. Default is 0.
    """

    def __init__(self, nodes, useMBoxes, numFlows=0):
        super(PathWithMbox, self).__init__(nodes, numFlows)
        self.useMBoxes = list(useMBoxes)

    @staticmethod
    def decode(dictionary):
        """
        Create a new path from a dict
        :param dictionary: dict type, must contain following keys:

            'nodes': maps to a list of nodes
            'useMBoxes': maps to a list of nodes at which middlebox is used
        """
        return PathWithMbox(dictionary['nodes'], dictionary['useMBoxes'], dictionary.get('numFlows', 0))

    def usesBox(self, node):
        """
        Check the path uses a given middlebox

        :param node: nodeID in question
        :return: True or False
        """
        return node in self.useMBoxes

    def fullLength(self):
        """

        :return: The full length of the path (includes all middleboxes)
        """
        return len(self._nodes) + len(self.useMBoxes)

    def encode(self):
        """
        Encode this path in dict/list form so it can be JSON-ed or MsgPack-ed

        :return: dictionary representation of this path
        """
        return {'nodes': self._nodes, 'numFlows': self._numFlows, 'useMBoxes': self.useMBoxes,
                'PathWithMbox': True}

    def __key(self):
        return tuple(self._nodes), tuple(self.useMBoxes), self._numFlows

    def __eq__(self, other):
        if not isinstance(other, PathWithMbox):
            return False
        return self._nodes == other._nodes and self.useMBoxes == other.useMBoxes

    def __repr__(self):
        return "PathWithMbox(nodes={}, useMBoxes={} numFlows={})". \
            format(str(self._nodes), self.useMBoxes, self._numFlows)