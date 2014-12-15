# coding=utf-8
""" Functions to manipulate the solution to the formulation
"""
import copy

import itertools


def getPathFractions(solvedProblem, ppk, flowCarryingOnly=True):
    """
    Gets flow fractions per each path from the solution

    :param solvedProblem: the Cplex object that has been solved
    :param ppk: paths per commodity dictionary
    :param flowCarryingOnly:
    :rtype: dict
    :returns: dictionary of paths to fractions """
    result = {}
    for commodity, paths in ppk.iteritems():
        result[commodity] = []
        for index, path in enumerate(paths):
            newpath = copy.copy(path)
            newpath.setNumFlows(solvedProblem.solution.get_values(
                'x_{}_{}'.format(commodity.ID, index)))
            if newpath.getNumFlows() > 0 and flowCarryingOnly:
                result[commodity].append(newpath)
            elif not flowCarryingOnly:
                result[commodity].append(newpath)
    return result


def getValueDict(solvedProblem):
    """ Get all the variables values

    :param solvedProblem: solved CPLEX problem instance
    :return: dictionary mapping of variable names to values
    """
    return dict(itertools.izip(solvedProblem.variables.get_names(),
                               solvedProblem.solution.get_values()))


def cleanSolutionPaths(topology, ppk):
    """
    Tweaks paths to get rid of super sinks and extra links between
    middleboxes and switches

    :param topology: topology
    :param ppk: paths per commodity
    :return: updated paths per commodity
    """
    G = topology.getGraph()
    newppk = copy.deepcopy(ppk)
    for k in newppk:
        for path in newppk[k]:
            for ind, n in enumerate(path):
                if topology.isMiddlebox(n):
                    path.getNodes().insert(ind + 1, path[ind - 1])
            e = path.getNodes()[-1]
            if 'superSink' in G.node[e]:
                path.getNodes().pop()
                k.dst = G.node[e]['sinkParent']
    return newppk


def getCPULoads(solvedProblem):
    res = {}
    for k, v in getValueDict(solvedProblem).iteritems():
        if k.startswith('cpuLoad_'):
            res[int(k.split('_')[-1])] = v
    return res