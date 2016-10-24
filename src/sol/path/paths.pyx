# coding=utf-8
"""
    Contains implementations of SOL Path objects
"""
import random
import numpy
from sol.utils.const import WARN_NO_PATH_ID
from sol.utils.ph import listeq
from paths cimport Path
from paths cimport PathWithMbox

from cpython cimport bool

# noinspection PyClassicStyleClass
cdef class Path:
    """ Represents a path in the network"""

    def __init__(self, nodes, pid=-1, flow_fraction=0):
        """Create a new path

        :param nodes: a list of node ids that belong to a path
        :param flow_fraction: the number of flows on this path
        """
        self._nodes = numpy.array(nodes)
        self._flowFraction = flow_fraction
        self._ID = pid
        if self._ID < 0:
            self._ID = random.randint(0, 1e6)
            numpy.warnings.warn(WARN_NO_PATH_ID)
        self._links = self._compute_links()

    cpdef int ingress(self):
        """
        :return: the ingress node of this path
        """
        return self._nodes[0]

    cdef _compute_links(self):
        return zip(self._nodes, self._nodes[1:])

    cpdef int egress(self):
        """
        :return: the egress node of this path
        """
        return self._nodes[-1]

    cpdef nodes(self):
        """
        :return: all nodes as a list
        """
        return self._nodes

    cpdef tuple iepair(self):
        """
        :return: ingress-egress pair for this path
        :rtype: tuple
        """
        return self.ingress(), self.egress()

    cpdef double flow_fraction(self):
        """
        :return: the number of flows on this path.
        """
        return self._flowFraction

    cpdef set_flow_fraction(self, double f):
        """
        Set number of flows on this path

        :param f: the new number of flows
        """
        self._flowFraction = f

    cpdef links(self):
        """
        :return: Return an iterator over the links in this path
        """
        # return zip(self._nodes, self._nodes[1:])
        return self._links

    cpdef int get_id(self):
        """
        Returns path id as int
        """
        return self._ID

    cpdef bool uses_box(self, node):
        return False

    cpdef dict encode(self):
        """
        Encode this path in dict/list form so it can be JSON-ed or MsgPack-ed

        :return: dictionary representation of this path
        """
        return {u'type': u'Path', u'id': self._ID,
                u'nodes': self._nodes.tolist(),
                u'flow_fraction': self._flowFraction}

    @staticmethod
    def decode(dict d):
        """
        Create a path from the dictionary representation
        :param d: the dictionary
        :return: a new Path instance
        """
        return Path(d[u'nodes'], d[u'id'], d[u'flow_fraction'])

    def __contains__(self, item):
        return item in self._nodes

    def __getitem__(self, item):
        return self._nodes[item]

    def __getslice__(self, int i, int j):
        return self._nodes[i:j]

    def __iter__(self):
        return iter(self._nodes)

    def __len__(self):
        """ Returns the length of the path as the number of hops in the path
        (this is equivalent to number of nodes in the path -1)
        """
        return len(self._nodes)-1

    def __repr__(self):
        return u"Path(nodes={}, flowFraction={})".format(str(self._nodes),
                                                        self._flowFraction)

    # noinspection PyProtectedMember
    def __richcmp__(Path self, other not None, int op):
        same_type = isinstance(other, Path)
        if op == 2:
            return same_type and listeq(self._nodes, other._nodes)
        elif op == 3:
            return not same_type or not listeq(self._nodes, other._nodes)
        else:
            raise TypeError

    def copy(self):
        return Path(self._nodes, self._ID, self._flowFraction)

    def __copy__(self):
        return self.copy()

# noinspection PyClassicStyleClass
cdef class PathWithMbox(Path):
    """
    Create a new path with middleboxes

    :param nodes: Path nodes (an ordered list)
    :param use_mboxes: At which nodes the middleboxes will be used
    :param flow_fraction: Fraction of flows along this path. Default is 0.
    """

    def __init__(self, nodes, use_mboxes, int pid=-1, flow_fraction=0):
        super(self.__class__, self).__init__(nodes, pid, flow_fraction)
        self.useMBoxes = list(use_mboxes)

    cpdef bool uses_box(self, node):
        """
        Check the path uses a given middlebox

        :param node: nodeID in question
        :return: True or False
        """
        return node in self.useMBoxes

    cpdef dict encode(self):
        """
        Encode this path in dict/list form so it can be JSON-ed or MsgPack-ed

        :return: dictionary representation of this path
        """
        return {u'nodes': self._nodes.tolist(),
                u'flow_fraction': self._flowFraction,
                u'use_mboxes': self.useMBoxes, u'id': self._ID,
                u'type': u'PathWithMBox'}

    @staticmethod
    def decode(dict d):
        """
        Create a new path from a dict
        :param d: dict type, must contain following keys:
        """
        return PathWithMbox(d[u'nodes'], d[u'use_mboxes'], d[u'id'],
                            d.get(u'flow_fraction', 0))

    # noinspection PyProtectedMember
    def __richcmp__(PathWithMbox self, other not None, int op):
        sametype = isinstance(other, PathWithMbox)
        if op == 2:
            return sametype and listeq(self._nodes, other._nodes) and \
                   listeq(self.useMBoxes, other.useMBoxes)
        elif op == 3:
            return not sametype or not listeq(self._nodes, other._nodes) \
                   or not listeq(self.useMBoxes, other.useMBoxes)
        else:
            raise TypeError

    def __repr__(self):
        return u"PathWithMbox(nodes={}, useMBoxes={} flowFraction={})". \
            format(str(self._nodes), self.useMBoxes, self._flowFraction)

    def copy(self):
        return PathWithMbox(self._nodes, self.useMBoxes, self._ID,
                            self._flowFraction)

    def __copy__(self):
        return self.copy()
