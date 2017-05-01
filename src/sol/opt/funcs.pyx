# coding=utf-8
"""
 Example functions for modeling link/node capacity constraints for use with the
 optimizations
"""


# noinspection PyUnusedLocal
import functools

# cpdef defaultLinkFunc(link, tc, path, resource, linkCaps):
#     """
#     Default link function that we use in all the optimizations
#
#     :param link: link for which multiplier is being computed
#     :param tc: the traffic class
#     :param path: the path
#     :param resource: the resource for which this is computed.
#         For simplicity assume this is just bandwidth
#     :param linkCaps: all link capacities
#     :return: volume of traffic in bytes normalized by link capacity
#     """
#     return tc.volBytes / linkCaps[link]
#
#
# # noinspection PyUnusedLocal
# cpdef defaultNodeCapFunc(node, tc, path, resource, nodeCaps):
#     """
#     Default node load function
#
#     :param node: nodeID
#     :param tc: the traffic class
#     :param path: path under consideration
#     :param resource: ignored, assumes we have only one resource (or all are the same)
#     :param nodeCaps: the node capacities for the resource
#     :return: cost of processing the traffic class for given resource, normalized by node capacity
#     """
#     return tc.volFlows * getattr(tc, '{}Cost'.format(resource)) / nodeCaps[node]
#
# cpdef defaultLinkFuncNoNormalize(link, tc, path, resource):
#     """
#     Default link function. Computes volume of bytes, does not normalize
#
#     :param link:
#     :param tc:
#     :param path:
#     :param resource:
#     :return: volume of this traffic class in bytes
#     """
#     return tc.volBytes
#
#
# cpdef defaultCostFunction(path):
#     """
#     Default path cost function, which is just the length of the path
#
#     :param path: path in question
#     :return: length of the path
#     """
#     return len(path)
#

def _const_cost(tc, path, node_or_link, cost):
    return tc.volFlows.compressed() * cost

def _dict_cost(tc, path, node_or_link, cost):
    return tc.volFlows.compressed() * cost[tc]

def _mbox_const(tc, path, node, cost):
    if path.uses_box(node):
        return tc.volFlows.compressed() * cost
    else:
        return 0

def _all_nodes_const(tc, path, node, cost):
    if node in path:
        return tc.volFlows.compressed() * cost
    else:
        return 0

class CostFuncFactory(object):
    @staticmethod
    def from_number(cost):
        return functools.partial(_const_cost, cost=cost)

    @staticmethod
    def from_dict(tc_to_cost):
        return functools.partial(_dict_cost, cost=tc_to_cost)

    @staticmethod
    def mbox_single_cost(cost):
        return functools.partial(_mbox_const, cost=cost)

    @staticmethod
    def all_nodes_single_cost(cost):
        return functools.partial(_all_nodes_const, cost=cost)