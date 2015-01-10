# coding=utf-8
"""
 Example functions for modeling link/node capacity constraints for use with the
 optimizations
"""


# noinspection PyUnusedLocal
def defaultLinkFunc(link, tc, path, resource, linkCaps):
    """
    Default link function that we use in all the optimizations

    :param link: link for which multiplier is being computed
    :param tc: the traffic class
    :param path: the path
    :param resource: the resource for which this is computed.
        For simplicity assume this is just bandwidth
    :param linkCaps: all link capacities
    :return: volume of traffic in bytes normalized by link capacity
    """
    return tc.volBytes / linkCaps[link]


# noinspection PyUnusedLocal
def defaultNodeCapFunc(node, tc, path, resource, nodeCaps):
    """
    Default node load function

    :param node: nodeID
    :param tc: the traffic class
    :param path: path under consideration
    :param resource: ignored, assumes we have only one resource (or all are the same)
    :param nodeCaps: the node capacities for the resource
    :return: cost of processing the traffic class for given resource, normalized by node capacity
    """
    return tc.volFlows * getattr(tc, '{}Cost'.format(resource)) / nodeCaps[node]

def defaultLinkFuncNoNormalize(link, tc, path, resource):
    """
    Default link function. Computes volume of bytes, does not normalize

    :param link:
    :param tc:
    :param path:
    :param resource:
    :return: volume of this traffic class in bytes
    """
    return tc.volBytes

# noinspection PyUnusedLocal
def dropUpstreamLinkFunc(link, tc, path, resource, linkCaps, dropRates, cumulative=False):
    """
    Example function for modeling link load while taking into account upstream
    drops

    :param link: the link for which the multiplier is computed
    :param tc: the traffic class
    :param path: the path
    :param resource: resource for which this is being computed
    :param linkCaps: all of the link capacities
    :type linkCaps: dict
    :param dropRates: drop rate (as fraction) at each node (as dict)
    :type dropRates: dict
    :param cumulative: If true, all nodes upstream contribute to the drop;
        if false, only the first node with non-zero drop contributes to the drop
    :return: volume of traffic in bytes normalized by link capacity, and taking into account upstream drops
    """
    retention = 1
    u, v = link
    droppedOnce = False
    for node in path:
        drop = dropRates.get(node, 0)
        if drop > 0:
            droppedOnce = True
        if not droppedOnce or cumulative:
            retention -= drop
        if node == v:
            break
    return tc.trafficClass.avgSize * tc.volume * retention / linkCaps[link]


def defaultCostFunction(path):
    """
    Default path cost function, which is just the length of the path

    :param path: path in question
    :return: length of the path
    """
    return len(path)
