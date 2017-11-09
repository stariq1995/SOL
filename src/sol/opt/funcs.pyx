# coding=utf-8
"""
 Example functions for modeling link/node capacity constraints for use with the
 optimizations
"""

# noinspection PyUnusedLocal
import functools

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
    """
    Generates cost resource consumption functions
    """

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
