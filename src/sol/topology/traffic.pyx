# coding=utf-8
""" Implements utility classes that have to do with traffic patterns, such as
network path, traffic matrix, and network commodities
"""
import random

from six.moves import zip


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
        return obj in self._nodes

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

    def __key(self):
        return tuple(self._nodes)

    def __eq__(self, other):
        if isinstance(other, Path):
            return self._nodes == other._nodes
        else:
            return False

    def __hash__(self):
        return hash(self.__key())

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


class TrafficMatrix(dict):
    """
    Represents a traffic matrix, extends basic dictionary type

    """

    def permute(self, rand=None):
        """
        Permute this traffic matrix randomly

        :param rand: instance of a Python :py:mod:`random` object
        """
        v = self.values()
        random.shuffle(v, rand)
        for i, k in enumerate(self.iterkeys()):
            self[k] = v[i]

class TrafficClass:
    """ Represents a traffic class. All members are public
    """

    # cdef public int ID, priority
    # cdef public char* name
    # cdef public double volFlows, volBytes
    # cdef public src, dst, srcIPPrefix, dstIPPrefix, srcAppPorts, dstAppPorts

    def __init__(self, ID, name, src, dst, volFlows=0, volBytes=0, priority=1,
                 srcIPPrefix=None, dstIPPrefix=None, srcAppPorts=None,
                 dstAppPorts=None, **kwargs):
        """ Creates a new traffic class. Any keyword arguments will be made into attributes.

        :param ID: unique traffic class identifier
        :param name: traffic class name, for human readability (e.g., 'web',
            'ssh', etc.)
        :param src: nodeID that is the ingress for this traffic class
        :param dst: nodeID that is the egress for this traffic class
        :param volFlows: number of flows for this traffic class
        :param volBytes: number of bytes for this traffic class
        :param priority: traffic class priority, as an integer (higher number means higher priority)
        :param srcIPPrefix: ingress IP prefix (CIDR notation)
        :param dstIPPrefix: egress IP prefix (CIDR notation)
        :param scrAppPorts: packet application ports (source)
        :param dstAppPorts: packet application ports (destination)
        """

        self.ID = ID
        self.name = name
        self.src = src
        self.dst = dst
        self.volFlows = volFlows
        self.volBytes = volBytes
        self.priority = priority
        self.srcIPPrefix = srcIPPrefix
        self.dstIPPrefix = dstIPPrefix
        self.srcAppPorts = srcAppPorts
        self.dstAppPorts = dstAppPorts

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return "TrafficClass({})".format(
            ",".join(["{}={}".format(k, v) for k, v in self.__dict__.iteritems()]))

    def __str__(self):
        return "Traffic class {} -> {}, {}, ID={}".format(self.src, self.dst,
                                                          self.name, self.ID)

    def encode(self):
        return {'TrafficClass': True}.update(self.__dict__)

    @staticmethod
    def decode(dict):
        return TrafficClass(**dict)

    def getIEPair(self):
        """
        Return the ingress-egress pair as a tuple

        :return:  ingress-egress pair
        :rtype: tuple
        """
        return self.src, self.dst

    def __key(self):
        """ Return the "identity of this object, so to speak"""
        return self.ID,

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if not isinstance(other, TrafficClass):
            return False
        else:
            return self.ID == other.ID