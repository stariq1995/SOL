# coding=utf-8
# cython: profile=True
"""
    Contains implementations of SOL Path objects
"""
import random

import numpy
from cpython cimport bool
from paths cimport Path
from paths cimport PathWithMbox
from six import itervalues, iterkeys, iteritems
from sol.utils.const import WARN_NO_PATH_ID
from sol.utils.ph import listeq
from collections import defaultdict
from sol.topology.traffic cimport TrafficClass

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
        """
        Whether the path uses a given middlebox. Returns False if the path
        is not an instance of PathWithMBox
        :param node:
        :return:
        """
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

    def __iter__(self):
        return iter(self._nodes)

    def __len__(self):
        """ Returns the length of the path as the number of hops in the path
        (this is equivalent to number of nodes in the path -1)
        """
        return len(self._nodes) - 1

    def __repr__(self):
        return u"Path(nodes={}, flowFraction={})".format(str(self._nodes),
                                                         self._flowFraction)

    # noinspection PyProtectedMember
    def __richcmp__(Path self, other not None, int op):
        same_type = isinstance(other, Path)
        if op == 2:
            return same_type and numpy.array_equal(self._nodes, other._nodes)
        elif op == 3:
            return not same_type or not numpy.array_equal(self._nodes, other._nodes)
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


cdef class PPTC:
    def __init__(self):
        self._data = dict()
        self._tcindex = dict()
        self._tcowner = dict()
        self._name_to_tcs = dict()

    cpdef add(self, name, TrafficClass tc, paths):
        # print paths
        # Strange workaound instead of directly calling numpy.ma.array(paths)
        # Because it was complaining about mismatched dimentions
        if isinstance(paths, numpy.ma.MaskedArray):
            self._data[tc] = paths
        else:
            self._data[tc] = numpy.empty(len(paths), dtype=object)
            for i in numpy.arange(len(paths)):
                self._data[tc][i] = paths[i]
            self._data[tc] = numpy.ma.array(self._data[tc])
        self._tcindex[tc.ID] = tc
        if name not in self._name_to_tcs:
            self._name_to_tcs[name] = set()
        self._name_to_tcs[name].add(tc)
        if tc not in self._tcowner:
            self._tcowner[tc] = {name}
        else:
            self._tcowner[tc].add(name)

    cpdef tcs(self, name=None):
        if name is None:
            return itervalues(self._tcindex)
        else:
            return iter(self._name_to_tcs[name])

    cpdef TrafficClass tc_byid(self, int tcid):
        return self._tcindex[tcid]

    cpdef paths(self, TrafficClass tc):
        return self._data[tc].compressed()

    cpdef all_paths(self, TrafficClass tc):
        return self._data[tc].data

    cpdef PPTC pptc(self, name):
        r = PPTC()
        for tc in self._name_to_tcs[name]:
            r.add(name, tc, self._data[tc])
        return r

    cpdef mask(self, TrafficClass tc, mask):
        # self.unmask()
        self._data[tc].mask = mask

    cpdef unmask(self, TrafficClass tc):
        self._data[tc].mask = numpy.ma.nomask

    cpdef clear_masks(self):
        for a in itervalues(self._data):
            a.mask = numpy.ma.nomask

    cpdef int num_paths(self, tc):
        return self._data[tc].size

    cpdef update(self, PPTC other):
        # NOTE: this is a shallow update
        for tc in other:
            self._data[tc] = other._data[tc]
            self._tcindex[tc.ID] = tc
            if tc not in self._tcowner:
                self._tcowner[tc] = set(other._tcowner[tc])
            else:
                self._tcowner[tc].add(other._tcowner[tc])
        for name, val in iteritems(other._name_to_tcs):
            if name in self._name_to_tcs:
                self._name_to_tcs[name].update(val)
            else:
                self._name_to_tcs[name] = val

    cpdef int max_paths(self):
        return max([x.size for x in itervalues(self._data)])

    cpdef int total_paths(self):
        return sum(map(len, itervalues(self._data)))

    cpdef int num_tcs(self):
        return len(self._data)

    cpdef copy(self):
        # TODO: Shallow copy here
        r = PPTC()
        r.update(self)

    cpdef bool empty(self):
        return len(self._data) == 0


    def __getitem__(self, item):
        return self.paths(item)

    def __iter__(self):
        return iterkeys(self._data)

    def __len__(self):
        raise AttributeError('len() is abiguious use num_tcs() or total_paths()')


    @staticmethod
    def merge(alist):
        if not all([isinstance(o, PPTC) for o in alist]):
            raise ValueError('All objects must be of PPTC type')
        result = PPTC()
        for a in alist:
            result.update(a)
        return result

    @staticmethod
    def from_dict(d, name):
        r = PPTC()
        for tc in d:
            r.add(name, tc, d[tc])
        return r



def path_decoder(o):
    if o[u'type'] == u'Path':
        return Path.decode(o)
    elif o[u'type'] == u'PathWithMBox':
        return PathWithMbox.decode(o)
    else:
        raise KeyError('Unknown path type')