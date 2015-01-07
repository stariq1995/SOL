# coding=utf-8

import networkx as nx

from sol.utils import exceptions
from ..topology.traffic import Path


def generatePathsPerIE(source, sink, topology, predicate, cutoff,
                       maxPaths=float('inf'), modifyFunc=None,
                       raiseOnEmpty=True):
    """
    Generates all simple paths between source and sink using a given predicate.

    :param source: the start node (source)
    :param sink: the end node (sink)
    :param topology: the topology on which we are operating
    :param predicate: the predicate that defines a valid path, must be a
       python callable that accepts a path and a topology, returns a boolean
    :param cutoff: the maximum length of a path.
        Helps to avoid unnecessarily long paths.
    :param maxPaths: maximum number of paths paths to return, by default no limit.
    :param modifyFunc: a custom function may be passed to convert a list of
        nodes, to a different type of path.

        For example, when choosing middleboxes, we use :py:func:`~predicates.useMboxModifier`
        to expand a list of switches into all possible combinations of middleboxes
    :param raiseOnEmpty: whether to raise an exception if no valid paths are detected.
        Set to True by default.
    :raise NoPathsException: if no paths are found
    :returns: a list of path objects
    :rtype: list
    """
    G = topology.getGraph()
    paths = []
    num = 0

    for p in nx.all_simple_paths(G, source, sink, cutoff):
        if modifyFunc is None:
            if predicate(p, topology):
                paths.append(Path(p))
                num += 1
        else:
            np = modifyFunc(p, topology)
            if isinstance(np, list):
                for innerp in np:
                    if predicate(innerp, topology):
                        paths.append(innerp)
                        num += 1
            else:
                if predicate(np, topology):
                    paths.append(np)
                    num += 1
        if num >= maxPaths:
            break
    if not paths:
        if raiseOnEmpty:
            raise exceptions.NoPathsException("No paths between {} and {}".format(source, sink))
    return paths


def generatePathsPerTrafficClass(topology, trafficClasses, predicate, cutoff,
                                 maxPaths=float('inf'), modifyFunc=None,
                                 raiseOnEmpty=True):
    """
    Generate all simple paths for each traffic class

    :param topology: topology to work with
    :param trafficClasses: a list of traffic classes for which paths should be generated
    :param predicate: predicate to use, must be a valid preciate callable
    :param cutoff:  the maximum length of a path.
    :param maxPaths: maximum number of paths paths to return, by default no limit.
    :param modifyFunc: a custom function may be passed to convert a list of
        nodes, to a different type of path.

        For example, when choosing middleboxes, we use :py:func:`~predicates.useMboxModifier`
        to expand a list of switches into all possible combinations of middleboxes
    :param raiseOnEmpty: whether to raise an exception if no valid paths are detected.
        Set to True by default.
    :raise NoPathsException: if no paths are found for a trafficClass
    :returns: a mapping of traffic classes to a list of path objects
    :rtype: dict
    """
    result = {}
    for t in trafficClasses:
        result[t] = generatePathsPerIE(t.src, t.dst, topology, predicate, cutoff, maxPaths,
                                       modifyFunc, raiseOnEmpty)
    return result


def generatePathsPerIE_stitching():
    """
    This is not yet implemented

    :raise: NotImplemented
    """
    # TODO: implement other ways of generating paths
    raise NotImplemented()


# def mergeppk(oldppk, newppk):
# """ Merges paths per commodity dictionaries by appending newppk to oldppk
# ..warning::
#         Requires dictionary keys (the commodities) to be the same in both
#         oldppk and newppk
#
#     :param oldppk: the original paths per commodity
#     :param newppk: the new paths per commodity to append
#     :return: the new dict containing merged paths per commodity
#     """
#     # assert len(set(oldppk.keys()).difference(newppk.keys())) == 0
#     result = {}
#     result.update(oldppk)
#     for k in newppk:
#         result[k].extend(newppk[k])
#     return result
