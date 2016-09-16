# coding=utf-8
""" Implements utility classes that have to do with traffic patterns, such as
    traffic matrix, and network traffic classes (commodities)
"""
import numpy as np
cimport numpy as np
from traffic cimport TrafficClass

cdef class TrafficClass(object):
    """ Represents a traffic class. All members are public
    """

    def __init__(self, int tcid, unicode name, int src, int dst,
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
        :param priority: traffic class priority, as an integer
            (higher number means higher priority)
        :param src_ip_prefix: ingress IP prefix (CIDR notation)
        :param dst_ip_prefix: egress IP prefix (CIDR notation)
        :param src_app_ports: packet application ports (source)
        :param dst_app_ports: packet application ports (destination)
        """

        self.ID = tcid
        self.name = name
        self.src = src
        self.dst = dst
        self.volFlows = np.ma.masked_array(data=vol_flows, mask=np.ma.nomask)
        self.volBytes = np.ma.masked_array(data=vol_bytes, mask=np.ma.nomask)
        # ensure that the volFlows and volBytes matches in size
        assert self.volFlows.size == self.volBytes.size
        self.priority = priority
        self.srcIPPrefix = src_ip_prefix
        self.dstIPPrefix = dst_ip_prefix
        self.srcAppPorts = src_app_ports
        self.dstAppPorts = dst_app_ports

    def __repr__(self):
        return "TrafficClass {} -> {}, {}, ID={}".format(self.src, self.dst,
                                                         self.name, self.ID)

    cpdef tuple iepair(self):
        """
        Return the ingress-egress pair as a tuple

        :return:  ingress-egress pair
        :rtype: tuple
        """
        return self.src, self.dst

    cpdef int ingress(self):
        """
        Return the ingress node for this traffic class
        :rtype: int
        """
        return self.src

    cpdef int egress(self):
        """
        Return the egress node for this traffic class
        :rtype: int
        """
        return self.dst

    def __hash__(self):
        return hash((self.ID, self.src, self.dst, self.name))

    def __richcmp__(TrafficClass self, other not None, int op):
        # This is a cython comparison function
        # Ensure that the other object is also a TrafficClass
        sametype = isinstance(other, TrafficClass)
        if op == 2: # this is equals opcode
            return sametype and (self.ID == other.ID and
                self.src == other.src and
                self.dst == other.dst and
                self.name == other.name)
        elif op == 3: # this is not equals opcode
            return not sametype or not (self.ID == other.ID and
                self.src == other.src and
                self.dst == other.dst and
                self.name == other.name)
        else:
            raise TypeError # we don't support such operations

    def __copy__(self):
        return TrafficClass(self.ID, self.name, self.src, self.dst,
                            self.volFlows, self.volBytes, self.priority,
                            self.srcIPPrefix, self.dstIPPrefix,
                            self.srcAppPorts, self.dstAppPorts)

    def encode(self):
        """
        Encode this traffic class into a dictionary, only with simple types
        in it.
        :return:
        """
        return {'type': 'TrafficClass', 'src': self.src, 'dst': self.dst,
                'name': self.name, 'id': self.ID}

    @staticmethod
    def decode(d):
        """
        Return a traffic calss from a given dictionary. Must contain
        'id', 'name', 'src' and 'dst' fields.
        :param d:
        :return:
        """
        return TrafficClass(d['id'], d['name'], d['src'], d['dst'])