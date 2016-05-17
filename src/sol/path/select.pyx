# coding=utf-8
""" Module implements different path pruning strategies
"""
import functools
import random
from collections import defaultdict
from sol.utils.exceptions import InvalidConfigException, SOLException

from sol.opt.composer cimport compose
from sol.topology.topologynx cimport Topology
from cpython cimport bool

_RANDOM = ['random', 'rand']
_SHORTEST = ['shortest', 'short', 'kshortest', 'k-shortest', 'kshort',
             'k-short']

cpdef choose_rand(dict pptc, int num_paths):
    """ Chooses a number of paths uniformly at random

    :param pptc: paths per commodity
    :param num_paths: number of paths to pick per commodity
    :return: the new (chosen) paths per each commodity
    :rtype: dict
    """
    newppk = {}
    for comm in pptc:
        if len(pptc[comm]) > num_paths:
            newppk[comm] = random.sample(pptc[comm], num_paths)
        else:
            newppk[comm] = pptc[comm]
    return newppk

cpdef sort_paths_per_commodity(dict pptc, key=None, bool inplace=True):
    """
    Sort paths per commodity

    :param pptc: paths per traffic class
    :param key: criteria to sort by. If none, path length is used
    :param inplace: sort in place. If False, new sorted ppk is returned.
    :return: New ppk if *inplace=False* otherwise None
    """
    if key is None:
        key = len
    if inplace:
        for tc in pptc:
            pptc[tc].sort(key=len)
    else:
        newppk = {}
        for tc in pptc:
            newppk[tc] = sorted(pptc[tc], key=key)
        return newppk

cpdef k_shortest_paths(pptc, int num_paths, bool needs_sorting=True,
                       bool inplace=True):
    """ Chooses K shortest paths
    :param pptc: paths per commodity
    :param num_paths: number of paths to choose (k) per commodity
    :param needs_sorting: whether we need to sort the paths first
    :param inplace: if *needs_sorting* is True, whether to sort the ppk in
        place or make a copy
    :return: the new (chosen) paths per commodity
    :rtype: dict
    """
    newppk = None
    if needs_sorting:
        newppk = sort_paths_per_commodity(pptc, key=len, inplace=inplace)
    if newppk is None:
        newppk = pptc
    result = {}
    for comm in pptc:
        result[comm] = newppk[comm][:num_paths]
    return result

# TODO: check that this is even used
def filter_paths(dict pptc, func):
    """ Filter paths using a function.

    :param pptc: paths per traffic class
    :param func: function to be applied to each path
    :return: new paths per commodity with paths for which *func* returned a
        true value
    """
    assert (hasattr(func, '__call__'))  # ensure this is a function
    result = defaultdict(lambda: [])
    for tc in pptc:
        for path in pptc[tc]:
            if func(path):
                result[tc].append(path)
    return result

def get_select_function(name, kwargs=None):
    """
    Return the path selection function based on name.
    Allows passing of additional keyword arguments, so that the returned function can satisfy the following signature::
        function(pptc, selectNumber)

    :param name: the name of the function
    :param kwargs: a dictionary of keyword arguements to be passed to the function
    :return: the callable object with
    :raise: InvalidConfigException
        if the name passed in is not supported

    Supported names so far: 'random' and 'shortest' For example::

        f = get_select_function('random')
        pptc = f(pptc, 5)

    will give you 5 paths per traffic class, randomly chosen

    """
    if kwargs is None:
        kwargs = {}
    if name.lower() in _RANDOM:
        return functools.partial(choose_rand, **kwargs)
    elif name.lower() in _SHORTEST:
        return functools.partial(k_shortest_paths, **kwargs)
    else:
        raise InvalidConfigException("Unknown select method")

# cpdef select_optimal(apps, Topology topo):
#     """
#     Select paths to be used for given apps on a given topology.
#     This is equivalent to the optimal solution.
#
#     :param apps: list of applications
#     :param topo: network topology
#     :return:
#     """
#     opt = compose(apps, topo)
#     opt.solve()
#     # Return paths
#     # FIXME: return them per app
#     return opt.getPathsFractions()

cdef _merge_pptc(apps):
    result = {}
    for app in apps:
        for tc in app.pptc:
            if tc not in result:
                result[tc] = app.pptc[tc]
    return result

cdef _filter_pptc(apps, chosen_pptc):
    for app in apps:
        for tc in app.pptc:
            app.pptc[tc] = chosen_pptc[tc]

cpdef select_robust(apps, Topology topo):
    """
    Select paths that are capable of supporting multiple traffic matrices
    :param apps:
    :param topo:
    :return:
    """
    opt = compose(apps, topo)
    mpptc = _merge_pptc(apps)  # merged
    opt.cap_num_paths(mpptc, (topo.num_nodes() - 1) ** 2 * 100)
    opt.solve()
    opt.write('select_robust')
    if not opt.is_solved():
        raise SOLException("Could not solve path selection problem for"
                           "topology %s" % topo.name)
    # get the paths chosen by the optimization
    # print (opt.get_var_values())
    chosen_pptc = opt.get_chosen_paths(mpptc)
    # print (chosen_pptc)
    # return paths by modifying the pptc of the apps they are associated with
    _filter_pptc(apps, chosen_pptc)
    return opt.get_time()

