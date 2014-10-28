# coding=utf-8
""" Implements utility classes that have to do with traffic patterns, such as
network path, traffic matrix, and network commodities
"""
from collections import defaultdict
import cPickle as pickle
import random

import yaml
import itertools


class Path(object):
    """ Represents a weighted path in a network"""

    def __init__(self, nodes, numFlows=0):
        """Create a new path

        :param nodes: a list of node ids that belong to a path
        :param numFlows: the number of flows on this path
        """
        self._nodes = list(nodes)
        self._numFlows = numFlows

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
        :return: the weight of this path.
        """
        return self._numFlows

    def setNumFlows(self, nflows):
        """
        Set the weight of this path
        :param nflows: the new number of flows
        """
        self._numFlows = nflows

    def getLinks(self):
        """
            Return an iterator over the links in this path
        """
        return itertools.izip(self._nodes, self._nodes[1:])

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
        return tuple(self._nodes), self._numFlows

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

    :param nodes:
    :param useMBoxes:
    :param numFlows:
    """

    def __init__(self, nodes, useMBoxes, numFlows=0):
        super(PathWithMbox, self).__init__(nodes, numFlows)
        if hasattr(useMBoxes, '__contains__') and hasattr(useMBoxes, '__len__'):
            self.useMBoxes = useMBoxes
        else:
            self.useMBoxes = [useMBoxes]

    def usesBox(self, node):
        """

        :param node:
        :return:
        """
        return node in self.useMBoxes

    # def __len__(self):
    def fullLength(self):
        return len(self._nodes) + len(self.useMBoxes)

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
    Represents a traffic matrix

    """

    # def __init__(self, arg):
    #     """ Creates a new traffic matrix.
    #
    #     :param arg:
    #         a dict mapping a 2-tuple (ingress, egress) to a number of flows
    #     """
    #     self._perODMatrix = arg
    #
    # def getODMatrix(self):
    #     """ Returns reference to the per OD traffic matrix """
    #     return self._perODMatrix

    def permute(self, rand=None):
        """
        Permute this traffic matrix randomly

        :param rand:
        """
        v = self.values()
        random.shuffle(v, rand)
        for i, k in enumerate(self.iterkeys()):
            self[k] = v[i]

    # def getODPairs(self):
    #     """
    #     :return: the ingress-egress pair of the perOD (perIE) traffic matrix
    #     :rtype: list of tuples
    #     """
    #     return self._perODMatrix.keys()
    #
    # def dumpToPickle(self, fobj):
    #     """  Write the traffic matrix to a pickle file
    #
    #     :param fobj: file-like object
    #     """
    #     pickle.dump(self._perODMatrix, fobj)
    #
    # def dumpToYAML(self, fobj):
    #     """
    #     Write the traffic matrix to a file (using yaml format)
    #
    #     :param fobj: file-like object
    #     """
    #     yaml.dump(self._perODMatrix, fobj)
    #
    # def dumpToPlainText(self, fobj):
    #     """
    #     Write the perOD traffic matrix to a plaintext file
    #
    #     :param fobj: file-like object
    #     """
    #     for k, v in self._perODMatrix.iteritems():
    #         fobj.write('{} {} {}\n'.format(k[0], k[1], v))
    #
    # @staticmethod
    # def loadFromYAML(fobj):
    #     """
    #     Load the traffic matrix from file
    #
    #     :param fobj: file-like object
    #     :return: the traffic matrix object
    #     """
    #     perODMatrix = yaml.load(fobj)
    #     t = TrafficMatrix(perODMatrix)
    #     return t
    #
    # @staticmethod
    # def loadFromPickle(fobj):
    #     """
    #     Load the traffic matrix from file
    #
    #     :param fobj: file-like object
    #     :return: the traffic matrix object
    #     """
    #     l = pickle.load(fobj)
    #     t = TrafficMatrix(l)
    #     return t
    #
    # @staticmethod
    # def loadFromPlaintext(fobj):
    #     """ Load the traffic matrix from plaintext file
    #     The format must be as follows:
    #     ingress egress volume
    #
    #     :param fobj: file-like object
    #     :return: the traffic matrix object
    #     """
    #     tm = {}
    #     for line in fobj:
    #         i, e, flows = line.split()
    #         tm[(int(i), int(e))] = float(flows)
    #     return TrafficMatrix(tm)
    #
    # def __repr__(self):
    #     return repr(self._perODMatrix)


class TrafficClass(object):
    """ Represents a traffic class.
    """

    def __init__(self, ID, name, src, dst, volFlows=0, volBytes=0, priority=1,
                 srcIPPrefix=None, dstIPPrefix=None, srcAppPorts=None,
                 dstAppPorts=None, **kwargs):
        """ Creates a new traffic class

        :param ID: unique traffic class identifier
        :param name: traffic class name, for human readability (e.g., 'web',
            'ssh', etc.)
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
            ",".join(["{}={}".format(k, v) for k, v in self.__dict__]))

    def __str__(self):
        return "Traffic class {} -> {}, {}, ID={}".format(self.src, self.dst,
                                                          self.name, self.ID)

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