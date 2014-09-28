""" This script pre-generates the commodities and paths for each of our
topologies so that formulation generation is quicker.
Also speeds up parsing the solutions.
"""

import networkx as nx

from ..topology.traffic import Path


def generatePathsPerIE(source, sink, topology, predicate, cutoff,
                       maxPaths=float('inf'), modifyFunc=None):
    """
    Generates all simple paths between source and sink using a given predicate.

    :param source: the start node (source)
    :param sink: the end node (sink)
    :param topology: the topology on which we are operating
    :param predicate: the predicate that defines a valid path, must be a
       python callable that accepts a path and a topology, returns a boolean
    :param maxPaths: maximum paths to return
    :param cutoff: the maximum length of a path
    :returns: a list of path objects
    :rtype: list
    """
    # Now generate all paths that match a predicate for each commodity
    G = topology.getGraph()
    # if cutoff is None:
    #     cutoff = int(ceil(nx.diameter(topology.getGraph().to_undirected()) *
    #                       1.7))
    paths = []
    num = 0
    # Are we dealing with a commodity where source == sink?
    if 'sinkParent' in G.node[sink] and source == G.node[sink]['sinkParent']:
        raise NotImplementedError("NOPE NOPE NOPE")
        # XXX this is untested
        # if yes, do a little hack
        # for neighbor in G[source]:
        #     for p in nx.all_simple_paths(G, source, neighbor, cutoff):
        #         p2 = p + [source, sink]
        #         if predicate(p2, topology):
        #             paths.append(Path(p2))
        #             num += 1
        #         if num >= maxPaths:
        #             break
    else:
        # if not, just compute the simple paths
        for p in nx.all_simple_paths(G, source, sink, cutoff):
            if predicate(p, topology):
                if modifyFunc is None:
                    paths.append(Path(p))
                    num += 1
                else:
                    np = modifyFunc(p, topology)
                    if isinstance(np, list):
                        paths.extend(np)
                        num += len(np)
                    else:
                        paths.append(np)
                        num += 1
            if num >= maxPaths:
                break
    if not paths:
        print 'No paths for:', source, sink
    return paths


# TODO: implement other ways of generating paths
def generatePathsPerIE_stitching():
    """  This is not yet implemented
    :return:
    :raise: NotImplemented
    """
    raise NotImplemented()


def mergeppk(oldppk, newppk):
    """ Merges paths per commodity dictionaries by appending newppk to oldppk
    ..note::
        Requires dictionary keys (the commodities) to be the same in both
        oldppk and newppk

    :param oldppk: the original paths per commodity
    :param newppk: the new paths per commodity to append
    :return: the new dict containing merged paths per commodity
    """
    # assert len(set(oldppk.keys()).difference(newppk.keys())) == 0
    result = {}
    result.update(oldppk)
    for k in newppk:
        result[k].extend(newppk[k])
    return result
