# coding=utf-8
"""
Module that implements different path selection (a.k.a pruning) strategies
"""
import functools
import random
from collections import defaultdict

import time
from itertools import combinations

from cpython cimport bool
from numpy import arange, power, exp, setdiff1d, inf, ceil, floor
from numpy import ma
from numpy.random import rand, choice
from six import iterkeys
from sol import logger
from sol.opt.composer import compose
from sol.topology.topologynx cimport Topology
from sol.utils.exceptions import InvalidConfigException, SOLException
from bitstring import BitArray

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

cpdef merge_pptc(apps, sort=False, key=None):
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
    if sort:
        sort_paths_per_commodity(result, key, inplace=True)
    return result

cdef _filter_pptc(apps, chosen_pptc):
    # Given a set of chosen pptc (global across all apps) modify the app's
    # internal pptc to reflect the chosen ones.
    for app in apps:
        for tc in app.pptc:
            app.pptc[tc] = chosen_pptc[tc]

cpdef select_ilp(apps, Topology topo, int num_paths=5, debug=False,
                 mode='weighted'):
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
    opt = compose(apps, topo, obj_mode=mode)
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
    """ Return a the probablity of accepting a new state """
    return 1 if oldo < newo else 1 / (exp(1.0 / temp))

cdef _obj_state(opt):
    return opt.get_solved_objective() if opt.is_solved() else -inf

cpdef select_sa(apps, Topology topo, int num_paths=5, int max_iter=20,
                double tstart=.72, double c=.88, logdb=None, mode='weighted'):
    """Select optimal paths using the simulated annealing search algorithm"""

    logger.info('Staring simulated annealing selection')
    # cdef int n = topo.num_nodes()
    # cdef unsigned int o = 0
    cdef double t = tstart
    # sort the paths by length
    allpaths = merge_pptc(apps, sort=True, key=len)
    tcind = {tc.ID: tc for tc in allpaths}

    # number of epochs
    cdef int nume = ma.compressed(next(iterkeys(allpaths)).volFlows).size

    pptc_len = {tc.ID: len(allpaths[tc]) for tc in allpaths}
    # pptcind = {}
    bs = {} # all bitstrings per traffic class
    bestopt = None
    opt = None
    bestpaths = {tcid: None for tcid in allpaths}
    cdef unsigned int accepted = 1 # whether the new state was accepted or not

    # This is to log our progress, for eval/debug purposes
    db = None
    if logdb is not None:
        import dataset
        db = dataset.connect(logdb).load_table('annealing')
        appnames=','.join([app.name for app in apps])

    cdef double start_time = time.time()

    # choose shortest paths first
    for tc in allpaths:
        b = BitArray(length=pptc_len[tc.ID])
        b.set(True, arange(min(num_paths, pptc_len[tc.ID])))
        bs[tc.ID] = []
        bs[tc.ID].append(BitArray(b))
    for a, app in enumerate(apps):
        for tc in app.pptc:
            app.pptc[tc] = [allpaths[tc][k]
                            for k in bs[tc.ID][0].findall('0b1')]
    # Create and solve the initial problem
    opt = compose(apps, topo, obj_mode=mode)
    opt.solve()
    # this is the best we have so far, even if it is unsolved
    bestopt = opt
    for tc in allpaths:
        bestpaths[tc.ID] = bs[tc.ID][0]

    # Log our initial state
    if db is not None:
        db.upsert(dict(topology=topo.name, num_paths=num_paths,
                       iteration=0, fairness=mode, appcombo=appnames,
                       obj=_obj_state(opt), time=time.time()-start_time,
                       maxiter=max_iter, temperature=t, accepted=accepted,
                       prob=1),
                  ['topology','num_paths','iteration','fairness','appcombo',
                   'maxiter'])

    logger.info('Starting SA simulation')
    for k in arange(1, max_iter):
        logger.info('k=%d/%d' % (k, max_iter))

        # Lower the temperature
        t = tstart * power(c, k)

        # Generate a new set of paths:
        replaced = False
        for tcid in bs:
            # nothing we can do if we don't have any new paths to substitute
            if num_paths >= pptc_len[tcid]:
                continue
            # if our current best optimization is unsolved, shift by one path
            if not bestopt.is_solved():
                newb = BitArray(bestpaths[tcid])
                newb >>= 1
                bs[tcid].append(newb)
                continue
            # otherwise check what paths have been unused by the best optimization
            goodpaths = []
            badpaths = []
            # TODO: optimize so this is only recomputed if we moved to a new accepted state
            for pindex in bestpaths[tcid].findall('0b1'):
                # The path should have been used in at least one epoch to be considered good
                if not all([bestopt.v('x_{}_{}_{}'.format(tcid, allpaths[tcind[tcid]][pindex].get_id(), e)).x == 0 for e in arange(nume)]):
                    goodpaths.append(pindex)
                else:
                    badpaths.append(pindex)
            # logger.debug('Good paths: %s' % goodpaths)
            # logger.debug('Bad paths: %s' % badpaths)
            # If all paths are good, keep them, move on
            if len(goodpaths) == num_paths:
                continue
            else: # Otherwise swap out bad paths for some new ones
                newb = BitArray(bestpaths[tcid])
                unused = list(newb.findall('0b0'))
                # logger.debug(unused)
                lpr = len(badpaths)
                # remove bad paths from last iteration
                newb.set(False, badpaths)

                # if not enough unused paths, just choose some randomly from the bad ones
                if len(unused) < lpr:
                    newb.set(False)
                    newb.set(True, unused)
                    newb.set(True, choice(badpaths, len(unused)-lpr, replace=False))
                else:
                    found = False
                    for bbb in combinations(unused, lpr):
                        newb.set(True, bbb)
                        if newb not in bs[tcid]:
                            found=True
                            break
                        else:
                            newb.set(False, bbb)
                    if not found:
                        # we've run out of possibilities, fall back to random
                        newb.set(True, choice(unused, lpr, replace=False))

                    # o = 0 # this is the offset into the unused paths
                    # # toggle the unused paths (up to the number we need to replace)
                    # newb.set(True, unused[o:lpr+o])
                    # # enter the loop if we already saw such combination
                    # # logger.debug('Unused: %s' % unused)
                    # while newb in bs[tcid] and o < len(unused) - lpr:
                    #     # logger.debug('%d: %s' % (tcid, newb.bin))
                    #     # toggle back to false
                    #     newb.set(False, unused[o:lpr+o])
                    #     o+=1 # increment offset
                    #     # toggle new set of unsued paths
                    #     newb.set(True, unused[o:lpr+o])
                    # # We went over
                    # if o >= len(unused) - lpr:


                    # logger.debug('final %d: %s' % (tcid, newb.bin))

                    assert newb.count(True) == min(num_paths, pptc_len[tcid])
                    bs[tcid].append(newb)
                    # m = max(pptc_len[tc.ID], ptr[tc.ID]+num_paths-len(goodpaths))
                    # pptcind[tcid].extend(arange(ptr[tc.ID], m))
                    # bs[tcid].extend(
                    #     choice(setdiff1d(arange(pptc_len[tcid]), goodpaths),
                    #            num_paths-len(goodpaths), replace=False))
                    replaced = True

        if not replaced:
            logger.info('No path replacement paths generated, done.')
            break

        # modify app pptc accoriding to indices
        for app in apps:
            for tc in app.pptc:
                app.pptc[tc] = [allpaths[tc][z] for z in bs[tc.ID][-1].findall('0b1') if
                                tc in app.pptc]

        opt = compose(apps, topo, obj_mode=mode)
        opt.solve()

        # if not opt.is_solved():
        #     logger.debug('No solution k=%d' % k)
        #     continue

        prob = _saprob(_obj_state(bestopt), _obj_state(opt), t)
        if prob >= rand():
            bestopt = opt
            for tcid in bs:
                bestpaths[tcid] = bs[tcid][-1]
            accepted = 1
        else:
            accepted = 0

        if db is not None:
            db.upsert(dict(topology=topo.name, num_paths=num_paths,
                           iteration=k, fairness=mode, appcombo=appnames,
                           obj=_obj_state(opt), time=time.time()-start_time,
                           maxiter=max_iter, temperature=t, accepted=accepted,
                           prob=prob),
                      ['topology','num_paths','iteration','fairness','appcombo',
                       'maxiter'])


    for app in apps:
        for tc in app.pptc:
            app.pptc[tc] = [allpaths[tc][k]
                            for k in bestpaths[tc.ID].findall('0b1')
                            if tc in app.pptc]
        # return paths based on s
    return bestopt, time.time() - start_time
