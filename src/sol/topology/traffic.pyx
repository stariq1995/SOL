# coding=utf-8
""" Implements utility classes that have to do with traffic patterns, such as
    traffic matrix, and network traffic classes (commodities)
"""
# import json
# import random
cimport numpy as np
from traffic cimport TrafficClass

# class TrafficMatrix(dict):
#     """
#     Represents a traffic matrix, extends basic dictionary type
#
#     """
#
#     def permute(self, rand=None):
#         """
#         Permute this traffic matrix randomly
#
#         :param rand: instance of a Python :py:mod:`random` object
#         """
#         v = self.values()
#         random.shuffle(v, rand)
#         for i, k in enumerate(self.iterkeys()):
#             self[k] = v[i]
#
#     def dump(self, fname):
#         """
#         Save the traffic matrix to a file
#         :param fname: filename to save to
#         """
#         with open(fname, 'w') as f:
#             json.dump({"{}->{}".format(k[0], k[1]): v for k, v in self.iteritems()}, f)
#
#     @staticmethod
#     def load(fname):
#         """
#         Load a traffic matrix from a file
#         :param fname: filename to load from
#         :return: a new TrafficMatrix
#         """
#         with open(fname, 'r') as f:
#             return TrafficMatrix({tuple(map(int, k.split('->'))): v for k, v in json.load(f).iteritems()})



cdef class TrafficClass(object):
    """ Represents a traffic class. All members are public
    """

    def __init__(self, int tcid, str name, int src, int dst,
                 np.ndarray vol_flows=np.zeros(1),
                 np.ndarray vol_bytes=np.zeros(1), int priority=1,
                 src_ip_prefix=None, dst_ip_prefix=None,
                 src_app_ports=None, dst_app_ports=None):
        """ Creates a new traffic class.

        :param tcid: unique traffic class identifier
        :param name: traffic class name, for human readability (e.g., 'web',
            'ssh', etc.)
        :param src: nodeID that is the ingress for this traffic class
        :param dst: nodeID that is the egress for this traffic class
        :param vol_flows: number of flows for this traffic class
        :param vol_bytes: number of bytes for this traffic class
        :param priority: traffic class priority, as an integer (higher number means higher priority)
        :param src_ip_prefix: ingress IP prefix (CIDR notation)
        :param dst_ip_prefix: egress IP prefix (CIDR notation)
        :param scrAppPorts: packet application ports (source)
        :param dst_app_ports: packet application ports (destination)
        """

        self.ID = tcid
        self.name = name
        self.src = src
        self.dst = dst
        self.volFlows = vol_flows
        self.volBytes = vol_bytes
        assert self.volFlows.size == self.volBytes.size
        self.priority = priority
        self.srcIPPrefix = src_ip_prefix
        self.dstIPPrefix = dst_ip_prefix
        self.srcAppPorts = src_app_ports
        self.dstAppPorts = dst_app_ports

    def __repr__(self):
        return "TrafficClass {} -> {}, {}, ID={}".format(self.src, self.dst,
                                                         self.name, self.ID)

    def get_iepair(self):
        """
        Return the ingress-egress pair as a tuple

        :return:  ingress-egress pair
        :rtype: tuple
        """
        return self.src, self.dst

    def __hash__(self):
        return hash((self.ID, self.src, self.dst, self.name))

    def __richcmp__(TrafficClass self, other not None, int op):
        sametype = isinstance(other, TrafficClass)
        if op == 2:
            return sametype and (self.ID == other.ID and
                                 self.src == other.src and
                                 self.dst == other.dst)
        elif op == 3:
            return not sametype or not (self.ID == other.ID and
                                        self.src == other.src and
                                        self.dst == other.dst)
        else:
            raise TypeError

    def __copy__(self):
        return TrafficClass(self.ID, self.name, self.src, self.dst,
                            self.volFlows, self.volBytes, self.priority,
                            self.srcIPPrefix, self.dstIPPrefix,
                            self.srcAppPorts, self.dstAppPorts)
