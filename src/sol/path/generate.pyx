# coding=utf-8
import itertools

from cpython cimport bool
from networkx import NetworkXNoPath
from sol.path.paths import PathWithMbox
from sol.topology.topologynx cimport Topology

from paths cimport Path, PPTC
from sol.utils import exceptions
from sol.utils.const import ERR_NO_PATH

cpdef use_mbox_modifier(path, int offset, Topology topology, chain_length=1):
    """
    Path modifier function. Expands one path into multiple paths, based on how many intermediate
    middleboxes are used.

    :param path: the path containing switch node IDs
    :param offset: the numeric id of the original path
    :param topology: the topology we are working with
    :param chain_length: how many middleboxes are required
    :return: a list of paths, note the special
        :py:class:`~sol.optimization.topology.traffic.PathWithMbox` object

    .. note::
        This with expand a single path into :math:`{n \\choose chainLength}`
        paths where :math:`n` is
        the number of switches with middleboxes attached to them in the current path.
    """
    return [PathWithMbox(path, chain, ind + offset) for ind, chain in
            enumerate(itertools.combinations(path, chain_length))
            if all([topology.has_middlebox(n) for n in chain])]

def generate_paths_ie(int source, int sink, Topology topology, predicate,
                      int cutoff, float max_paths=float('inf'),
                      modify_func=None, bool raise_on_empty=True):
    """
    Generates all simple paths between source and sink using a given predicate.

    :param source: the start node (source)
    :param sink: the end node (sink)
    :param topology: the topology on which we are operating
    :param predicate: the predicate that defines a valid path, must be a
       python callable that accepts a path and a topology, returns a boolean
    :param cutoff: the maximum length of a path.
        Helps to avoid unnecessarily long paths.
    :param max_paths: maximum number of paths paths to return, by default no limit.
    :param modify_func: a custom function may be passed to convert a list of
        nodes, to a different type of path.

        For example, when choosing middleboxes, we use :py:func:`~predicates.use_mbox_modifier`
        to expand a list of switches into all possible combinations of middleboxes
    :param raise_on_empty: whether to raise an exception if no valid paths are detected.
        Set to True by default.
    :raise NoPathsException: if no paths are found
    :returns: a generator over the path objects
    """
    # paths = []
    num = 0

    try:
        for p in topology.paths(source, sink, cutoff):
            if modify_func is None:
                if predicate(p, topology):
                    # paths.append(Path(p, num))
                    num += 1
                    yield Path(p, num)
                else:
                    continue
            else:
                np = modify_func(p, num, topology)
                if isinstance(np, list):
                    for innerp in np:
                        if predicate(innerp, topology):
                            # paths.append(innerp)
                            num += 1
                            yield innerp
                        else:
                            continue
                else:
                    if predicate(np, topology):
                        # paths.append(np)
                        num += 1
                        yield np
                    else:
                        continue
            if num >= max_paths:
                return
    except NetworkXNoPath:
        if raise_on_empty:
            raise exceptions.NoPathsException(ERR_NO_PATH.format(source, sink))
        else:
            return
    # print("num == %d" % num)
    if num == 0 and raise_on_empty:
        raise exceptions.NoPathsException(ERR_NO_PATH.format(source, sink))

cpdef PPTC generate_paths_tc(Topology topology, traffic_classes, predicate,
                             cutoff,
                             max_paths=float('inf'), modify_func=None,
                             raise_on_empty=True, name=None):
    """
    Generate all simple paths for each traffic class

    :param topology: topology to work with
    :param traffic_classes: a list of traffic classes for which paths should be generated
    :param predicate: predicate to use, must be a valid preciate callable
    :param cutoff:  the maximum length of a path.
    :param max_paths: maximum number of paths paths to return, by default no limit.
    :param modify_func: a custom function may be passed to convert a list of
        nodes, to a different type of path.

        For example, when choosing middleboxes, we use :py:func:`~predicates.use_mbox_modifier`
        to expand a list of switches into all possible combinations of middleboxes
    :param raise_on_empty: whether to raise an exception if no valid paths are detected.
        Set to True by default.
    :param name: name of the owner for these traffic classes (and paths)
    :raise NoPathsException: if no paths are found for a trafficClass
    :returns: a mapping of traffic classes to a list of path objects
    :rtype: dict
    """
    if name is None:
        name = 'noname'
    result = PPTC()
    for t in traffic_classes:
        result.add(name, t, list(generate_paths_ie(t.src, t.dst, topology,
                                                   predicate, cutoff,
                                                   max_paths, modify_func,
                                                   raise_on_empty)))
    return result
