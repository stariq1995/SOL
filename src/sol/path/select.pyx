# coding=utf-8
"""
Module that implements different path selection (a.k.a pruning) strategies
"""
import functools
import random
from collections import defaultdict

import time
from cpython cimport bool
from numpy import arange, power, exp, setdiff1d
from numpy import ma
from numpy.random import rand, choice
from six import iterkeys
from sol import logger
from sol.opt.composer cimport compose
from sol.topology.topologynx cimport Topology
from sol.utils.exceptions import InvalidConfigException, SOLException

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
        newppk = {}  # make a new objet
        for tc in pptc:
            newppk[tc] = sorted(pptc[tc], key=key)  # ensure that list is new
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
    :raise: :py:class:`sol.utils.exceptions.InvalidConfigException`
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

cpdef select_ilp(apps, Topology topo, int num_paths=5, debug=False):
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
    logger.info('Selection composition')
    opt = compose(apps, topo)
    mpptc = merge_pptc(apps)  # merged
    opt.cap_num_paths(mpptc, (topo.num_nodes() - 1) ** 2 * num_paths)
    logger.info('Selection solving')
    opt.solve()
    if debug:
        opt.write('debug/select_ilp_{}'.format(topo.name))
    if not opt.is_solved():
        raise SOLException("Could not solve path selection problem for "
                           "topology %s" % topo.name)
    if debug:
        opt.write_solution('debug/select_ilp_solution_{}'.format(topo.name))
    # get the paths chosen by the optimization
    # print (opt.get_var_values())
    chosen_pptc = opt.get_chosen_paths(mpptc)
    # print (chosen_pptc)
    # return paths by modifying the pptc of the apps they are associated with
    _filter_pptc(apps, chosen_pptc)
    return opt, opt.get_time()

cdef inline double _saprob(oldo, newo, temp):
    return 1 if oldo < newo else 1 / (1 + exp(-(newo - oldo) / temp))

cdef _obj_state(opt):
    return opt.get_solved_objvalue()

cpdef select_sa(apps, Topology topo, int num_paths=5):
    logger.info('SA selection')
    cdef int n = topo.num_nodes()
    cdef int kmax = 500/num_paths # 500 paths per traffic class
    cdef double tstart = 1000, t = tstart
    allpaths = merge_pptc(apps)
    tcind = {tc.ID: tc for tc in allpaths}

    cdef int nume = ma.compressed(next(iterkeys(allpaths)).volFlows).size

    per_tc_lengths = {tc.ID: len(allpaths[tc]) for tc in allpaths}
    # print(per_tc_lengths)
    # cdef ndarray pptcind = empty((len(apps), len(allpaths), num_paths))
    pptcind = {}
    bestopt = None
    opt = None
    bestpaths = None
    start_time = time.time()
    # choose random indices, and setup the legths array
    while bestopt is None:
        for a, app in enumerate(apps):
            for tc in app.pptc:
                pptcind[tc.ID] = choice(arange(per_tc_lengths[tc.ID]),
                                        min(num_paths, per_tc_lengths[tc.ID]),
                                        replace=False)

                app.pptc[tc] = [allpaths[tc][k] for k in pptcind[tc.ID]]
        # solve initial state
        opt = compose(apps, topo)
        opt.solve()
        if opt.is_solved():
            bestopt = opt
            bestpaths = pptcind.copy()
        else:
            logger.info('No solution for initial state')

    logger.info('Starting SA simulation')
    for k in arange(kmax):
        logger.info('k=%d/%d' % (k, kmax))
        # generate a new set of paths
        # first take existing paths
        replaced = False
        for tcid in pptcind:
            # nothing we can do if we don't have any paths to replace with
            if num_paths >= per_tc_lengths[tcid]:
                continue
            # if last optimization is unsolved, go to a random state
            if not opt.is_solved():
                logger.info("Previous iteration had no solution")
                pptcind[tc.ID] = choice(arange(per_tc_lengths[tc.ID]),
                                        min(num_paths, per_tc_lengths[tc.ID]),
                                        replace=False)
                replaced = True
            # otherwise check what paths have been unused by the last optimization
            else:
                goodpaths = [pindex for i, pindex in enumerate(pptcind[tcid])
                             if not all([opt.v('x_{}_{}_{}'.format(tcid,
                                                                   allpaths[tcind[tcid]][pindex].get_id(), e)).x == 0
                             for e in arange(nume)])]
                if len(goodpaths) == num_paths:
                    continue
                pptcind[tcid] = goodpaths
                pptcind[tcid].extend(
                    choice(setdiff1d(arange(per_tc_lengths[tcid]), goodpaths),
                           num_paths-len(goodpaths), replace=False))
                replaced = True

        if not replaced:
            logger.info('No path replacement paths generated, done.')
            break

        # modify app pptc accoriding to indices
        for app in apps:
            for tc in app.pptc:
                app.pptc[tc] = [allpaths[tc][z] for z in pptcind[tc.ID] if
                                tc in app.pptc]

        opt = compose(apps, topo)
        opt.solve()
        if not opt.is_solved():
            logger.debug('No solution k=%d' % k)
            continue

        if _saprob(bestopt.get_solved_objective(),
                   opt.get_solved_objective(), t) >= rand():
            bestopt = opt
            bestpaths = pptcind.copy()
        t = tstart * power(.95, k)

    for app in apps:
        for tc in app.pptc:
            app.pptc[tc] = [allpaths[tc][k] for k in bestpaths[tc.ID] if
                            tc in app.pptc]
        # return paths based on s
    return bestopt, time.time() - start_time
