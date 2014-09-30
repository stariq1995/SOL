"""
 Example functions for modeling link/node capacity constraints for use with the
 optimizations
"""


def curryLinkConstraintFunc(func, *args, **kwargs):
    """
    Curries the link constraint functions

    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    return lambda x, y, z: func(x, y, z, *args, **kwargs)


# noinspection PyUnusedLocal
def defaultLinkFunc(k, path, link, linkcaps):
    """
    Default link function that we use in all the optimizations

    :param k: the commodity
    :param path: the path
    :param link: link for which $x_p$ multiplier is being computed
    :param linkcaps: all link capacities
    :return:
    """
    return k.trafficClass.avgSize * k.volume / linkcaps[link]


def dropUpstreamLinkFunc(k, path, link, linkcaps, dropRates, cumulative=False):
    """
    Example function for modeling link load while taking into account upstream
    drops

    :param k: commodity
    :param path: the path
    :param link: the link for which the multiplier is computed
    :param linkcaps: all of the link capacities
    :type linkcaps: dict
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
    return k.trafficClass.avgSize * k.volume * retention / linkcaps[link]