# coding=utf-8
"""
 Example functions for modeling link/node capacity constraints for use with the
 optimizations
"""


# noinspection PyUnusedLocal
def defaultLinkFunc(link, tc, path, resource, linkCaps):
    """
    Default link function that we use in all the optimizations

    :param link: link for which $x_p$ multiplier is being computed
    :param tc: the traffic class
    :param path: the path
    :param resource: the resource for which this is computed.
        For simplicity assume this is just bandwidth
    :param linkCaps: all link capacities
    :return: the multiplier
    """
    return tc.volBytes / linkCaps[link]


def defaultNodeCapFunc(node, tc, path, resource, nodeCaps):
    """
    Default node load function

    :param node: node for which $x_p$ multiplier is being computed
    :param tc: the traffic class
    :param path: path under consideration
    :param resource: ignored, assumes we have only one resource (or all are the same)
    :param nodeCaps: the node capacities for the resource
    :return: the multiplier
    """
    return tc.volFlows * getattr(tc, '{}Cost'.format(resource)) / nodeCaps[node]


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
    :return: $x_p$ multiplier
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

def defaultSomeNodesFunction(path):
    """
    Simple function that requires at least one node to be enabled on the path

    :param path: path in question
    :return: number of nodes to be enabled (as int) before traffic can flow
    """
    return 1
