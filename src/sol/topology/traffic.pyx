# coding=utf-8
""" Implements utility classes that have to do with traffic patterns, such as
network path, traffic matrix, and network commodities
"""
import random


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

