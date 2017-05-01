# coding=utf-8
# cython: profile=True
"""
Module that implements different path selection (a.k.a pruning) strategies
"""
import random
import time
from collections import defaultdict
from itertools import combinations, cycle

from cpython cimport bool
from numpy cimport ndarray
from numpy import arange, power, inf, mean, ones, bitwise_xor, \
    array, argsort, ma
from numpy.random import choice
from six import iterkeys, iteritems
from sol.opt.composer cimport compose_apps
from sol.path.paths cimport PPTC
from sol.path.paths import PathWithMbox, Path
from sol.topology.topologynx cimport Topology
from sol.topology.traffic cimport TrafficClass
from sol.utils.ph import noop

from sol.utils.const import *
from sol.utils.exceptions import SOLException
from sol.utils.logger import logger

_RANDOM = ['random', 'rand']
_SHORTEST = ['shortest', 'short', 'kshortest', 'k-shortest', 'kshort',
             'k-short']

cpdef choose_rand(PPTC pptc, int num_paths):
    """
    Chooses a specified number of paths per traffic class uniformly at
    random

    :param pptc: paths per traffic class
    :param int num_paths: number of paths to pick per traffic class
    :return: the new (chosen) paths per traffic class
    :rtype: dict

    """
    logger.debug('Choosing paths randomly')
    cdef TrafficClass tc
    cdef int n
    cdef ndarray mask
    for tc in pptc:
        n = pptc.all_paths(tc).size
        # Sample only if the number of available paths is larger than
        # given number
        if n > num_paths:
            mask = ones(n)
            mask[choice(arange(n), num_paths, replace=False)] = 0
            pptc.mask(tc, mask)
        else:
            pptc.unmask(tc)


cpdef k_shortest_paths(PPTC pptc, int num_paths, bool ret_mask=False):
    """ Chooses :math:`k` shortest paths per traffic class

    :param pptc: paths per traffic class
    :param int num_paths: number of paths to choose ($k$) per traffic class
    :param ret_mask: return the mask after the paths have been masked. False by default
    """

    masks = {}
    for tc in pptc:
        # Get lengths of all paths, even the masked ones (thus the second .data access)
        lens = array([len(x) for x in pptc._data[tc].data])
        # Sort lengths and only return indices
        ind = argsort(lens)
        # Create an array mask, with everything masked
        mask = ones(pptc.num_paths(tc, all=True), dtype=bool)
        # Unmask the shortest paths
        mask[ind[:min(num_paths, mask.size)]] = 0
        pptc.mask(tc, mask)
        # Store the mask in case we need to return it
        masks[tc] = mask
    if ret_mask:
        return masks


# TODO: find a way to select paths that preserves flow affinity (for mboxes)

cpdef select_ilp(apps, Topology topo, network_config, int num_paths, debug=False,
                 fairness=Fairness.WEIGHTED, epoch_mode=EpochComposition.WORST):
    """
    Global path selection function. This chooses paths across multiple applications
    for the given topology, under a global cap for total number of paths.

    :param apps: list of applications for which we are selecting paths
    :param topo: network topology
    :param network_config: the network configuration (e.g., global network capacities)
    :param num_paths: number of paths per traffic class to choose.
        This is used as a guideline for computing total path cap!
        The actual **selected** number of paths might be more or less
        depending on the ILP solution
    :param fairness: the type of fairness to use when composing applications
    :param epoch_mode: type of cross-epoch composition. Leaving the default (which is optimizing for the worst case)
        is usually acceptable.
    :param debug: if True, output additional debug information,
        and write ILP+results to disk.

    :return: None, the applications' :py:attr:`sol.App.pptc` attribute will
        be modified to reflect selected paths.

    """
    logger.info('Selection composition')
    start_time = time.time()
    opt = compose_apps(apps, topo, network_config, fairness=fairness,
                       epoch_mode=epoch_mode)
    opt.cap_num_paths((topo.num_nodes() - 1) ** 2 * num_paths)
    logger.info('Solving ILP selection problem')
    opt.solve()
    if debug:
        opt.write('debug/select_ilp_{}'.format(topo.name))
    if not opt.is_solved():
        raise SOLException("Could not solve path selection problem for "
                           "topology %s" % topo.name)
    if debug:
        opt.write_solution('debug/select_ilp_solution_{}'.format(topo.name))
    # get the paths chosen by the optimization
    # This will mask paths according to selection automatically:
    opt.get_chosen_paths()


def _path_score(path):
    pass

def select_greedy(pptc, topo, resource_order, resource_weights=None):

    pass


def greedy_search(ndarray paths, topo, resource_order, resource_weights=None):
    pass


class PathTree(object):
    """
    Internal class to help track path replacements when using simulated annealing
    """
    def __init__(self, ndarray paths):
        if isinstance(paths[0], PathWithMbox):
            self.buckets = defaultdict(lambda: [])
            for pi, p in enumerate(paths):
                for m in p.mboxes():
                    self.buckets[m].append(pi)
            if self.buckets:
                for k in self.buckets:
                    self.buckets[k] = array(self.buckets[k])
            # cyclical iterator over all the buckets.
            # a dictionary with cyclic iterators inside each bucket
            self.inner_iters = {b: cycle(v) for b, v in iteritems(self.buckets)}

        elif isinstance(paths[0], Path):
            _pathlen = array([len(x) for x in paths])
            # only one bucket for the
            self.buckets = dict()
            self.inner_iters = dict()
            self.buckets[0] = argsort(_pathlen)
            self.inner_iters[0] = cycle(self.buckets[0])
        else:
            raise TypeError('Unknown path type submitted for indexing')
        self.bucket_iter = cycle(iterkeys(self.buckets))

    def next(self):
        """
        Return the next path index.
        :return:
        """
        # get next bucket
        b = next(self.bucket_iter)
        # next path from the bucket
        return next(self.inner_iters[b])


cdef inline double _saprob(oldo, newo, temp):
    """ Return a the probablity of accepting a new state """
    return 1 if oldo <= newo else 0  # 1 / (exp(1.0 / temp))

cdef _obj_state(opt):
    return opt.get_solved_objective() if opt.is_solved() else -inf


class ExpelMode(IntEnum):
    """
    Represents path expel modes when using 
    simulated annealing path selection
    """
    no_flow = 1 # Kick out paths that do not carry any flow
    inverse_flow = 2 # Kick out paths with probability inverse proportional to the flow fraction
    random = 3 # Kick out random paths
    all = 4 # Kick out all paths and sample fresh


class ReplaceMode(IntEnum):
    """
    Represents the replacement strategies for paths 
    when using simulated annealing
    """
    next_sorted = 1
    # edge_disjoint = 2
    random = 3
    pathtree = 4
    greedy = 5

cdef _expel(tcid, existing_mask, xps, mode=ExpelMode.no_flow):
    """
    Kick out paths by masking them in the pptc 
    :param tcid: traffic class for which this is performed
    :param existing_mask: existing path mask (for the given traffic class).
        This mask will be modified in-place (no copy)!
    :param xps: all the x_* variables from the last available optimization
    :param mode: expel mode, see :py:class:ExpelMode
    :return: the updated mask, which is really a pointer to the existing_mask
    """
    cdef int ii = 0, i
    if mode == ExpelMode.no_flow:
        for i, maskval in enumerate(existing_mask):
            if not maskval:  # the value was unmasked and path was used
                if not any([x.x != 0 for x in xps[tcid, ii, :] if not isinstance(x, int)]):
                    existing_mask[i] = 1  # mask it, it was useless path
                ii += 1
    elif mode == ExpelMode.inverse_flow:
        for i, maskval in enumerate(existing_mask):
            if not maskval:  # the value was unmasked and path was used
                flow = mean([x.x for x in xps[tcid, ii, :] if not isinstance(x, int)])
                # sample uniformly at random; if low enough kick the path anyway
                # flow == 0 -> 100% probability of getting expelled
                # flow == 1, 1-1 = 0 -> 0% of getting expelled
                # flow == .3, 1-.3 = .7 -> 70% probability of getting expelled
                if random.random() <= 1.0 - flow:
                    existing_mask[i] = 1  # mask it, it was useless path
                ii += 1
    elif mode == ExpelMode.random:
        for i, maskval in enumerate(existing_mask):
            if not maskval:  # the value was unmasked and path was used
                if random.random() < .5:  # toss a coin
                    existing_mask[i] = 1  # mask it, it was useless path
    elif mode == ExpelMode.all:
        existing_mask.fill(1)
    else:
        raise ValueError('Unsupported annealing expel mode: %s' % mode)
    return existing_mask

cdef bool _in(ndarray mask, explored):
    """
    Check that the existing mask (i.e., path combination has been used before)
    
    .. warning::
        This is dependent on mask arrays being of dtype bool
        We XORing the arrays here (for speed) and bool arrays give us the results
        we expect.
    
    :param mask: path mask (combination) to check
    :param explored: previously explored combinations 
    :return: True or False 
    """
    cdef ndarray x
    for x in explored:
        if (bitwise_xor(mask, x) == 0).all():
            return True
    return False

cdef _replace(explored, mask, num_paths,
              mode=ReplaceMode.next_sorted, tree=None):
    """
    Replace paths by picking some and adding them to the mask.
    For a single traffic class
    
    :param explored: Paths that have already been explored/used 
    :param mask: the current path mask (after paths have been expelled)
    :param num_paths: number of paths we want
    :param mode: replacement mode
    :param tree: if the replacement mode is pathtree, provide the tree here
    :return: 
    """
    cdef int num_tries = 0, max_tries = 100, i = 0
    # Number of paths that still need to be enabled
    replace_len = max(0, num_paths - ((mask == 0).sum()))
    if replace_len <= 0:
        return

    # these are indices of our next possible choices
    unused = [i for i, v in enumerate(mask) if v == 1]
    # if not enough unused paths, just enable all paths
    if len(unused) < replace_len:
        mask[:] = 0
        return
    if mode == ReplaceMode.next_sorted:
        # Just keep going down the list of paths
        # XXX: this assumes paths have been sorted by length in increasing order
        found_new = False
        for comb in combinations(unused, replace_len):
            # print comb
            mask[list(comb)] = 0
            # print mask
            if not _in(mask, explored):
                found_new = True
                break
            else:
                mask[list(comb)] = 1
        if not found_new:
            logger.debug("{} ran out of possibilites, falling back to {}".format(
                mode.name, ReplaceMode.random.name))
            # we've run out of possibilities, fall back to random
            mask[choice(unused, replace_len, replace=False)] = 0
    elif mode == ReplaceMode.random:
        comb = choice(unused, replace_len, replace=False)
        mask[comb] = 0
        while not _in(mask, explored) and num_tries < max_tries:
            mask[comb] = 1
            comb = choice(unused, replace_len, replace=0)
            mask[comb] = 0
            num_tries += 1
    elif mode == ReplaceMode.pathtree:
        comb = set()
        while len(comb) < replace_len:
            comb.add(next(tree))
        comb = list(comb)
        mask[comb] = 0
        while _in(mask, explored) and num_tries < max_tries:
            mask[comb] = 1
            comb = set()
            while len(comb) < replace_len:
                comb.add(next(tree))
            comb = list(comb)
            mask[comb] = 0
            num_tries += 1
            # if num_tries >= max_tries:
            #     logger.error('Pathtree method could not find new combo after %d tries' % max_tries)
    # elif mode == ReplaceMode.edge_disjoint:
    #     raise NotImplementedError("")
    else:
        raise ValueError('Unsupported annealing replace mode: %s' % mode)

cdef _get_mboxes(x):
    return x.mboxes()


# cdef _compute_temp_schedule(int max_iter, )

cpdef select_sa(apps, Topology topo, network_config, int num_paths=5, int max_iter=20,
                double tstart=.72, double c=.88, logdb=None,
                fairness=Fairness.WEIGHTED,
                epoch_mode=EpochComposition.WORST,
                expel_mode=ExpelMode.no_flow,
                replace_mode=ReplaceMode.next_sorted,
                select_config=None, debug=False):
    """
    Select optimal paths using the simulated annealing search algorithm
    """

    logger.info('Starting simulated annealing selection')
    logger.debug('Replace mode %s' % replace_mode)
    # Starting temperature and probability of acceptance
    cdef double t = tstart, prob
    # Merge all paths
    all_pptc = PPTC.merge([a.pptc for a in apps])
    # compute number of epochs
    cdef int nume = ma.compressed(next(all_pptc.tcs()).volFlows).size
    # compute length of paths per each traffic class
    pptc_len = {tc: all_pptc.num_paths(tc) for tc in all_pptc.tcs()}
    explored = {}  # all explored combos per traffic class
    bestopt = None  # best available optimization
    opt = None  # current optimization
    bestpaths = {tc: None for tc in all_pptc.tcs()}  # indices of best paths
    cdef unsigned int accepted = 1  # whether the new state was accepted or not
    cdef int k = 0

    # Log our progress, for eval/debug purposes
    db = None
    config_id = None
    if logdb is not None:
        import pymongo
        client = pymongo.MongoClient(logdb.host, logdb.port)
        cl = client['solier']
        db = cl['annealing']
        # solutions = cl['solutions']
        select_configs = cl['select_configs']
        config_id = select_configs.find_one(select_config)['_id']
        # Cleanup old state
        db.delete_many({'config_id': config_id})
        # solutions.delete_many({'config_id': config_id})

    cdef double start_time = time.time()
    cdef double opt_time = 0

    # choose shortest paths first
    initial_masks = k_shortest_paths(all_pptc, num_paths, ret_mask=True)
    for tc in initial_masks:
        explored[tc] = [initial_masks[tc]]

    # build the pathtrees for each traffic class
    pathtrees = {}
    if replace_mode == ReplaceMode.pathtree:
        for tc in all_pptc.tcs():
            pathtrees[tc] = PathTree(all_pptc.all_paths(tc))
    else:
        for tc in all_pptc.tcs():
            pathtrees[tc] = None

    # Create and solve the initial problem
    opt = compose_apps(apps, topo, network_config, fairness=fairness, epoch_mode=epoch_mode)
    opt.solve()
    opt_time += opt.get_time()

    if debug:
        opt.write('debug/annealing_{}_{}'.format(topo.name, k))

    # We need to find at least one acceptable state
    try:
        from progressbar import ProgressBar, UnknownLength
        bar = ProgressBar(max_value=UnknownLength)
    except ImportError:
        bar = None
    while not opt.is_solved() and k <= max_iter:
        # resample paths:
        for tc in all_pptc.tcs():
            newmask = _expel(tc.ID, explored[tc][-1], None, ExpelMode.all)
            _replace(explored[tc], newmask, num_paths, replace_mode,
                     tree=pathtrees[tc])
            explored[tc].append(newmask)
        # Re-run opt
        opt = compose_apps(apps, topo, network_config, fairness=fairness, epoch_mode=epoch_mode)
        opt.solve()
        opt_time += opt.get_time()
        k += 1
        if bar is not None:
            bar.update(k)
    if k > max_iter:
        raise SOLException("Could not solve the base simulated annealing problem after %d iterations" % max_iter)

    # this is the best we have so far
    bestopt = opt
    for tc in all_pptc.tcs():
        bestpaths[tc] = explored[tc][-1]

    # Log our initial state
    if db is not None:
        val = dict(obj=_obj_state(opt), solvetime=opt.get_time(), time=time.time() - start_time,
                   temperature=t, accepted=accepted, iteration=0, config_id=config_id)
        db.insert(val)
        # solution = opt.get_solution()
        # solution.update(config_id=config_id, iteration=0)
        # solutions.insert(solution)

        # db.upsert(dict(topology=topo.name, num_paths=num_paths,
        #                iteration=0, fairness=mode, appcombo=appnames,
        #                obj=_obj_state(opt), time=time.time() - start_time,
        #                maxiter=max_iter, temperature=t, accepted=accepted,
        #                prob=1, expel_mode=expel_mode, replace_mode=replace_mode),
        #           ['topology', 'num_paths', 'iteration', 'fairness', 'appcombo',
        #            'maxiter', 'expel_mode', 'replace_mode'])

    logger.info('Starting SA simulation')
    try:
        from progressbar import ProgressBar
        bar = ProgressBar()
    except ImportError:
        bar = noop
    for k in bar(arange(1, max_iter)):
        # Lower the temperature
        t = tstart * power(c, k)

        # Generate a new set of paths
        # Get exisiting path fractions first
        optvars = bestopt.get_xps()
        for tc in explored:
            # nothing we can do if we don't have any new paths to substitute
            if num_paths >= pptc_len[tc]:
                continue
            # otherwise check what paths have been unused by the best optimization
            newmask = _expel(tc.ID, bestpaths[tc].copy(), optvars,
                             expel_mode)
            _replace(explored[tc], newmask, num_paths, replace_mode, tree=pathtrees[tc])
            # modify app pptc accoriding to indices
            all_pptc.mask(tc, newmask)
            explored[tc].append(newmask)

        opt = compose_apps(apps, topo, network_config, fairness=fairness, epoch_mode=epoch_mode)
        opt.solve()
        opt_time += opt.get_time()
        if debug:
            opt.write('debug/annealing_{}_{}'.format(topo.name, k))

        if not opt.is_solved():
            logger.debug('No solution k=%d' % k)
            if db is not None:
                db.insert_one(dict(solvetime=opt.get_time(), time=time.time() - start_time,
                                   temperature=t, accepted=0, iteration=k, config_id=config_id))
            continue

        prob = _saprob(_obj_state(bestopt), _obj_state(opt), t)
        if random.random() <= prob:
            bestopt = opt
            for tc in explored:
                bestpaths[tc] = explored[tc][-1]
            accepted = 1
        else:
            accepted = 0

        if db is not None:
            val = dict(obj=_obj_state(opt), solvetime=opt.get_time(), time=time.time() - start_time,
                       temperature=t, accepted=accepted, iteration=k, config_id=config_id)
            db.insert(val)

    for tc in all_pptc:
        all_pptc.mask(tc, bestpaths[tc])

    return bestopt, time.time() - start_time, opt_time
