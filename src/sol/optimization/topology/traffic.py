""" Implements utility classes that have to do with traffic patterns, such as
network path, traffic matrix, and network commodities
"""
from collections import defaultdict
import cPickle as pickle
import random

import yaml


class Path(object):
    """ Represnts a weighted path in a network"""

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
        assert isinstance(other, PathWithMbox)
        return self._nodes == other._nodes and self.useMBoxes == \
                                                other.useMBoxes

    def __repr__(self):
        return "PathWithMbox(nodes={}, useMBoxes={} numFlows={})".format(str(
            self._nodes),
                                                                         self.useMBoxes,
                                                                         self._numFlows)


class TrafficMatrix(object):
    """ Represents a traffic matrix
    Has two internal representations (not necessarily consistent with each
    other, be warned!) a per IE pair (perOD) traffic matrix and the per path
    traffic matrix
    """

    def __init__(self, arg):
        """ Creates a new traffic matrix.

        :param arg: One of the following traffic matrix representations:
            * a list of path objects with weights (perPath TM)
            * a dict mapping a 2-tuple (ingress, egress) to a float (weight)
        """
        if isinstance(arg, list) and isinstance(arg[0], Path):
            self._perPathMatrix = arg
            self._perODMatrix = defaultdict(lambda: 0)
            for path in arg:
                self._perODMatrix[path.getIEPair()] += path.getWeight()
        elif isinstance(arg, dict):
            self._perODMatrix = arg
            self._perPathMatrix = None
        else:
            raise Exception('Invalid constructor arguments')

    def getPathMatrix(self):
        """ Returns reference to the per path traffic matrix """
        return self._perPathMatrix

    def getODMatrix(self):
        """ Returns reference to the per OD traffic matrix """
        return self._perODMatrix

    def convertODtoPathMatrix(self, paths):
        """ Take the per OD traffic matrix and assign weights to the provided
        paths, resulting in a per path traffic matrix. Note that if there are
        multiple paths between a single OD pair, traffic will be split
        uniformly between the paths.

        .. warning::
           this will modify the paths and store the matrix internally.

        :param paths: a list of Path objects to assign weights to
        :returns: per path traffic matrix
        :rtype: dict
        """
        odpaths = defaultdict(lambda: [])
        for path in paths:
            odpaths[path.getIEPair()].append(path)
        for k, v in odpaths.iteritems():
            for path in v:
                path.setNumFlows(1.0 / len(v) * self._perODMatrix[
                    path.getIEPair()])
        self._perPathMatrix = list(paths)
        return self._perPathMatrix

    def permute(self):
        k, v = map(list,zip(*self._perODMatrix.iteritems()))
        # print k,v
        random.shuffle(v)
        self._perODMatrix = dict(zip(k, v))
        if self._perPathMatrix is not None:
            #TODO: test this
            self._perPathMatrix = self.convertODtoPathMatrix(self._perPathMatrix)

    def getODPairs(self):
        """
        :return: the ingress-egress pair of the perOD (perIE) traffic matrix
        :rtype: list of tuples
        """
        return self._perODMatrix.keys()


    def dumpToPickle(self, fobj):
        """  Write the traffic matrix to a pickle file

        :param fobj: file-like object
        """
        pickle.dump([dict(self._perODMatrix), self._perPathMatrix],
                    fobj)

    def dumpToYAML(self, fobj):
        """
        Write the traffic matrix to a file (using yaml format)

        :param fobj: file-like object
        """
        yaml.dump([self._perODMatrix, self._perPathMatrix], fobj)

    def dumpToPlainText(self, fobj):
        """
        Write the perOD traffic matrix to a plaintext file

        :param fobj: file-like object
        """
        for k, v in self._perODMatrix.iteritems():
            fobj.write('{} {} {}\n'.format(k[0], k[1], v))


    @staticmethod
    def loadFromYAML(fobj):
        """
        Load the traffic matrix from file

        :param fobj: file-like object
        :return: the traffic matrix object
        """
        l = yaml.load(fobj)
        t = TrafficMatrix(l[0])
        t._perPathMatrix = l[1]
        return t

    @staticmethod
    def loadFromPickle(fobj):
        """
        Load the traffic matrix from file

        :param fobj: file-like object
        :return: the traffic matrix object
        """
        l = pickle.load(fobj)
        t = TrafficMatrix(l[0])
        t._perPathMatrix = l[1]
        return t

    @staticmethod
    def loadFromPlaintext(fobj):
        """ Load the traffic matrix from plaintext file
        The format must be as follows:
        ingress egress volume

        :param fobj: file-like object
        :return: the traffic matrix object
        """
        # TODO: implement plaintext loading
        raise NotImplemented()


    def __repr__(self):
        return repr(self._perODMatrix)


class Commodity(object):
    """Class that represents a commodity.
    Has src, dst and volume of traffic (in sessions) between src and dst as
    well as associated class if any
    """

    def __init__(self, ID, src, dst, trafficClass, volume=0, weight=1,
                 srcprefix=None, dstprefix=None):
        """ Create a new commodity

        :param ID: the commodity ID
        :param src: source node (ingress)
        :param dst: destination node (egress)
        :param trafficClass: the traffic class associated with this commodity
        :param volume: volume as number of flows
        :param weight: a commodity priority
        """
        self.ID = ID
        self.src = src
        self.dst = dst
        self.volume = volume
        self.trafficClass = trafficClass
        self.weight = weight
        self.srcprefix = srcprefix
        self.dstprefix = dstprefix

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
        if not isinstance(other, Commodity):
            return False
        else:
            return self.ID == other.ID

    def __repr__(self):
        return "Commodity(ID={},src={},dst={},traffiClass={},volume={}," \
               "weight={})".format(self.ID, self.src, self.dst,
                                   self.trafficClass.name, self.volume,
                                   self.weight)


class TrafficClass(object):
    """ Represents a traffic class. Traffic class should have the following
    attributes: name, fraction of total traffic, average
    size per flow.  Other optional values include resource footprint (cost)
    """

    def __init__(self, name, fraction, avgSize, extraAttr=None):
        """ Creates a new traffic class

        :param name: traffic class name
        :param fraction: fraction of total traffic this
        :param avgSize: average flow size
        :param extraAttr: dict with any additional attributes
        """
        self.name = name
        self.fraction = fraction
        self.avgSize = avgSize
        self.extra = extraAttr
        if self.extra is None:
            self.extra = dict()

    def __getitem__(self, item):
        return self.extra[item]

    def __setitem__(self, key, value):
        self.extra[key] = value

    def __contains__(self, item):
        return item in self.extra
