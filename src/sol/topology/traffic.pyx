# coding=utf-8
""" Implements utility classes that have to do with traffic patterns, such as
    traffic matrix, and network traffic classes (commodities)
"""
import json
import random
from traffic cimport TrafficClass


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

    def dump(self, fname):
        """
        Save the traffic matrix to a file
        :param fname: filename to save to
        """
        with open(fname, 'w') as f:
            json.dump({"{}->{}".format(k[0], k[1]): v for k, v in self.iteritems()}, f)

    @staticmethod
    def load(fname):
        """
        Load a traffic matrix from a file
        :param fname: filename to load from
        :return: a new TrafficMatrix
        """
        with open(fname, 'r') as f:
            return TrafficMatrix({tuple(map(int, k.split('->'))): v for k, v in json.load(f).iteritems()})


cdef class TrafficClass(object):
    """ Represents a traffic class. All members are public
    """

    def __init__(self, int ID, str name, int src, int dst, double volFlows=0, double volBytes=0, int priority=1,
                 srcIPPrefix=None, dstIPPrefix=None, srcAppPorts=None, dstAppPorts=None):
        """ Creates a new traffic class.

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

    def __repr__(self):
        return "TrafficClass {} -> {}, {}, ID={}".format(self.src, self.dst,
                                                         self.name, self.ID)

    def getIEPair(self):
        """
        Return the ingress-egress pair as a tuple

        :return:  ingress-egress pair
        :rtype: tuple
        """
        return self.src, self.dst

    def __hash__(self):
        return hash((self.ID, self.src, self.dst, self.name))

    def __richcmp__(TrafficClass self, other not None, int op):
        sameType = isinstance(other, TrafficClass)
        if op == 2:
            return sameType and (self.ID == other.ID and self.src == other.src and self.dst == other.dst)
        elif op == 3:
            return not sameType or not (self.ID == other.ID and self.src == other.src and self.dst == other.dst)
        else:
            raise TypeError

    def __copy__(self):
        return TrafficClass(self.ID, self.name, self.src, self.dst, self.volFlows, self.volBytes, self.priority,
                            self.srcIPPrefix, self.dstIPPrefix, self.srcAppPorts, self.dstAppPorts)
