# coding=utf-8
"""
Module that implements different path selection (a.k.a pruning) strategies
"""
import functools
import random
from collections import defaultdict

from sol.utils.exceptions import InvalidConfigException, SOLException
from sol.opt.composer cimport compose
from sol.topology.topologynx cimport Topology
from cpython cimport bool

# Common string names for the path selection strategies. Must all be defined
# and compared in lower case.
_RANDOM = ['random', 'rand']
_SHORTEST = ['shortest', 'short', 'kshortest', 'k-shortest', 'kshort',
             'k-short']

cpdef choose_rand(dict pptc, int num_paths):
    """
    Chooses a specified number of paths per traffic class uniformly at
    random

    :param dict pptc: paths per traffic class
    :param int num_paths: number of paths to pick per traffic class
    :return: the new (chosen) paths per traffic class
    :rtype: dict
    """
    newppk = {}
    for comm in pptc:
        # Sample only if the number of available paths is larger than
        # given number
        if len(pptc[comm]) > num_paths:
            newppk[comm] = random.sample(pptc[comm], num_paths)
        else:
            newppk[comm] = pptc[comm]
    return newppk

cpdef sort_paths_per_commodity(dict pptc, key=None, bool inplace=True):
    """
    Sort paths per commodity

    :param dict pptc: paths per traffic class
    :param key: criteria to sort by. If None, path length is used
    :param bool inplace: boolean, whether to sort in place.
        If False, a new mapping is returned.
    :return: a dictionary if *inplace=False*, otherwise None
    """
    if key is None:
        key = len  # default is to use path length
    if inplace:
        for tc in pptc:
            pptc[tc].sort(key=len)
    else:
        newppk = {} # make a new objet
        for tc in pptc:
            newppk[tc] = sorted(pptc[tc], key=key) # ensure that list is new
        return newppk

cpdef k_shortest_paths(pptc, int num_paths, bool needs_sorting=True,
                       bool inplace=True):
    """ Chooses $k$ shortest paths per traffic class

    :param dict pptc: paths per traffic class
    :param int num_paths: number of paths to choose ($k$) per traffic class
    :param bool needs_sorting: whether we need to sort the paths before selection.
        True by default
    :param bool inplace: if *needs_sorting* is True, whether to sort the ppk in
        place or make a copy. Default is True.
    :return: the new (chosen) paths per traffic class
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

# TODO: check that this method is even used, might be obsolete
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
    Allows passing of additional keyword arguments, so that the returned
    function can satisfy the following signature::
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

cpdef merge_pptc(apps):
    """
    Merge paths per traffic class (:py:attr:`sol.opt.app.App.pptc`)
    from different apps into a single dictionary.

    ..warning:
        If applications share traffic classes, paths for shared traffic classes
        will be taken from the first encountered application.

        This shouldn't cause problems since paths for the same traffic class
        *should* be identical, but beware in case they are not!

    :param list apps: list of :py:class:`sol.opt.app.App` objects
    :return: paths per traffic class dictionary
    :rtype: dict
    """
    result = {}
    for app in apps:
        for tc in app.pptc:
            if tc not in result:
                result[tc] = app.pptc[tc]
    return result

cdef _filter_pptc(apps, chosen_pptc):
    # Given a set of chosen pptc (global across all apps) modify the app's
    # internal pptc to reflect the chosen ones.
    for app in apps:
        for tc in app.pptc:
            app.pptc[tc] = chosen_pptc[tc]

cpdef select_ilp(apps, Topology topo, num_paths=5, debug=False):
    """
    Global path selection function. This chooses paths across multiple applications
    for the given topology, under a global cap for total number of paths.

    :param apps: list of applications for which we are selecting paths
    :param topo: network topology
    :param num_paths: number of paths per traffic class to choose.
        This is used as a guideline for computing total path cap!
        The actual **selected** number of paths might be more or less
        depending on the ILP solution
    :param debug: if True, output additional debug information,
        and write ILP/results
        to disk.

    :return: None, the applications' :py:attr:`sol.opt.App.pptc` attribute will
        be modified to reflect selected paths.
    """
    opt = compose(apps, topo, 'sum')
    mpptc = merge_pptc(apps)  # merged
    opt.cap_num_paths(mpptc, (topo.num_nodes() - 1) ** 2 * 5)
    opt.solve()
    if debug:
        opt.write('debug/select_ilp')
    if not opt.is_solved():
        raise SOLException("Could not solve path selection problem for"
                           "topology %s" % topo.name)
    if debug:
        opt.write_solution('debug/select_robust_solution')
    # get the paths chosen by the optimization
    # print (opt.get_var_values())
    chosen_pptc = opt.get_chosen_paths(mpptc)
    # print (chosen_pptc)
    # return paths by modifying the pptc of the apps they are associated with
    _filter_pptc(apps, chosen_pptc)
    return opt.get_time()
