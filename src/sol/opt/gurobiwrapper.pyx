# coding=utf-8
# cython: profile=True
# cython: linetrace=True
"""
Wrapper around Gurobi
"""
from __future__ import division, print_function

try:
    # noinspection PyPackageRequirements
    from gurobipy import *
except ImportError as e:
    print(ERR_NO_GUROBI)
    raise e

import copy
import time

import numpy
from numpy import ma, zeros, ones, full, extract, where, arange, array, \
    frompyfunc
from six import iterkeys, iteritems, itervalues, next
from six.moves import range
from cpython cimport bool
from sol.utils.exceptions import SOLException
from sol.utils.ph import Tree
from sol.path.paths cimport Path
from sol.topology.traffic cimport TrafficClass
from sol.topology.topologynx cimport Topology
from gurobiwrapper cimport OptimizationGurobi
from sol.opt.varnames cimport xp, al, bn, be, bp
from sol.utils.const import RES_LATENCY, OBJ_MAX_ALL_FLOW, ALLOCATE_FLOW, \
    CAP_LINKS, \
    CAP_NODES, OBJ_MIN_LINK_LOAD, OBJ_MIN_LATENCY, MIN_NODE_LOAD, ROUTE_ALL, \
    RES_NOT_LATENCY
from sol.utils.logger import logger
from itertools import chain

OBJ_MAX_LINK_SPARE_CAP = u'maxlinkspare'
OBJ_MAX_NODE_SPARE_CAP = u'maxnodespare'
OBJ_MAX_NOT_LATENCY = u'maxnotlatency'

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:
    """
    Represents a SOL optimization problem.
    Uses Gurobi for building and solving the model.
    """
    def __init__(self, Topology topo, all_pptc, bool measure_time=True):
        self.opt = Model()
        # This will disable console output
        self.opt.params.LogToConsole = 0
        self.opt.ModelSense = GRB.MAXIMIZE
        # Keeps track of the resource loads symbolically
        self.expr = {}
        self.topo = topo
        # Keeps track of all variables
        self._varindex = {}
        # Should we measure the time it takes to solve the optimization
        self._do_time = measure_time
        self._time = 0
        self._load_dict = Tree()
        res_set = set()
        for elem in chain(topo.nodes(), topo.links()):
            res_set.update(topo.get_resources(elem))
        self._res_dict = {r: i for i, r in enumerate(res_set)}
        # self._xps = Tree()
        if len(set([ma.compressed(x.volFlows).size for x in
                    iterkeys(all_pptc)])) != 1:
            raise ValueError(
                'Number of epochs is inconsistent across traffic classes')
        self.num_epochs = ma.compressed(next(iterkeys(all_pptc)).volFlows).size
        cdef int max_paths = max(map(len, itervalues(all_pptc)))
        self._xps = full((len(all_pptc), max_paths, self.num_epochs), 0,
                         dtype=object)
        self._load_array = zeros((len(res_set), topo.num_nodes(),
                                  topo.num_nodes(),
                                  len(all_pptc), max_paths, self.num_epochs))

        logger.debug("Initialized Gurobi wrapper")

    cpdef _add_decision_vars(self, dict pptc):
        """
        Add desicision variables of the form x_* responsible for determining the amount
        of flow on each path for each trafficlass (and potentially per each epoch).

        :param pptc:
        :return:
        """
        cdef TrafficClass tc
        cdef int epoch, pathid
        cdef unicode name
        # cdef bool mod = False

        for tc in pptc:
            for pathid in arange(len(pptc[tc])):
                for epoch in arange(self.num_epochs):
                    if self._xps[tc.ID, pathid, epoch] == 0:
                        self._xps[tc.ID, pathid, epoch] = self.opt.addVar(0, 1)

        # if not self._has_var(name):
        #     self._varindex[name] = self.opt.addVar(lb=0, ub=1,
        #                                            name=name)
        #     mod = True
        # if mod:
        self.opt.update()
        logger.debug("Added desicion vars")

    cdef _add_binary_vars(self, dict pptc, vtypes):
        cdef unicode name
        cdef Path p
        cdef bool mod = False
        for t in vtypes:
            if t.lower() == u'node':
                for n in self.topo.nodes(False):
                    name = bn(n)
                    if not self._has_var(name):
                        self._varindex[name] = self.opt.addVar(vtype=GRB.BINARY,
                                                               name=name)
                        mod = True
            elif t.lower() == u'edge':
                for u, v in self.topo.links(False):
                    name = be(u, v)
                    if not self._has_var(name):
                        self._varindex[name] = self.opt.addVar(vtype=GRB.BINARY,
                                                               name=name)
                        mod = True
            elif t.lower() == u'path':
                for tc in pptc:
                    for p in pptc[tc]:
                        name = bp(tc, p)
                        if not self._has_var(name):
                            self._varindex[name] = self.opt.addVar(
                                vtype=GRB.BINARY, name=name)
                            mod = True
            else:
                raise SOLException("Unknown binary variable type")
        if mod:
            self.opt.update()

    cpdef allocate_flow(self, pptc, allocation=None):
        """
        Allocate network flow for each traffic class by allocating flow on each
        path (and summing it up for each traffic class)

        :param pptc: paths per traffic class
        :param allocation: if given, allocation for given traffic classes will
            be set to this value. Allocation must be between 0 and 1
        :raises: ValueError if the given allocation is not between 0 and 1
        """
        self._add_decision_vars(pptc)
        cdef int pi
        cdef int epoch = 0, num_epochs = ma.compressed(
            next(iterkeys(pptc)).volFlows).size
        cdef unicode name
        cdef TrafficClass tc
        for tc in pptc:
            for epoch in range(num_epochs):
                name = al(tc, epoch)
                self._varindex[name] = self.opt.addVar(lb=0, ub=1, name=name)
        self.opt.update()
        if allocation is None:
            for tc in pptc:
                for epoch in range(num_epochs):
                    name = al(tc, epoch)
                    lhs = LinExpr()
                    # for path in pptc[tc]:
                    # lhs.addTerms(1, self.v(xp(tc, path, epoch)))
                    ind = self._xps[tc.ID, :, epoch].nonzero()
                    vars = self._xps[tc.ID, :, epoch][ind]

                    lhs.addTerms(ones(vars.size),
                                 vars)
                    self.opt.addConstr(lhs == self.v(name))
        else:
            raise NotImplemented()
            if not 0 <= allocation <= 1:
                raise ValueError(ERR_ALLOCATION)
            for tc in pptc:
                for epoch in range(num_epochs):
                    name = self.al(tc, epoch)
                    self.opt.addConstr(self.v(name) == allocation)
        self.opt.update()

    cpdef route_all(self, pptc):
        """
        Ensure that all available traffic is routed (no drops)
        by forcing the allocation of flow to be 1
        for all of the given traffic classes.

        :param pptc: paths per traffic class
        """
        cdef int epoch = 0, num_epochs = ma.compressed(
            next(iterkeys(pptc)).volFlows).size
        cdef unicode name
        for tc in pptc:
            for epoch in range(num_epochs):
                name = al(tc, epoch)
                v = self.v(name)
                v.lb = v.ub = 1
        self.opt.update()

        # cdef _consume_helper(self, tc, path, node_or_link, int num_epochs,
        #                      unicode prefix, unicode resource_name, double cost, caps):
        #     cdef unicode name
        #     cdef int epoch
        #     for epoch in range(num_epochs):
        #         self.expr[resource_name][node_or_link][epoch][tc].append
        # for epoch in range(num_epochs):
        #     name = '{}_{}'.format(prefix, epoch)
        #     if not self._has_var(name):
        #         self._varindex[name] = self.opt.addVar(name=name, ub=1)
        #     v = self.v(xp(tc, path, epoch))
        #     if self.expr[resource_name][node_or_link][epoch] is None:
        #         self.expr[resource_name][node_or_link][epoch] = LinExpr()
        #     self.expr[resource_name][node_or_link][epoch].addTerms(
        #         tc.volFlows.compressed()[epoch] * cost / caps[node_or_link], v)
        # self.opt.update()

    cpdef consume(self, pptc, unicode resource, double cost, node_caps,
                  link_caps):
        """
        :param pptc: paths per traffic class
        :param resource: resource to be consumed
        :param cost: cost per flow for this resource
        """
        logger.debug(u'Consume: %s' % resource)
        # cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        logger.debug(u'Num epochs in consume: %d' % self.num_epochs)
        cdef int e, pathid
        cdef int res_index = self._res_dict[resource]

        for tc in pptc:
            vols = tc.volFlows.compressed()
            for pathid, path in enumerate(pptc[tc]):
                for node in node_caps:
                    if path.uses_box(node):
                        # for e in range(num_epochs):
                        # self._load_dict[resource][node][e][tc][
                        #     self.v(xp(tc, path, e))] = vols[e] * cost / \
                        #                                node_caps[node]

                        self._load_array[
                        res_index, node, node, tc.ID, pathid, :] = \
                            vols * cost / node_caps[node]

                for link in path.links():
                    u, v = link
                    if link in link_caps:
                        # for e in range(num_epochs):
                        # self._load_dict[resource][link][e][tc][
                        #     self.v(xp(tc, path, e))] = vols[e] * cost / \
                        #                                link_caps[link]
                        self._load_array[
                        res_index, u, v, tc.ID, pathid, :] = \
                            vols * cost / link_caps[link]

    cpdef cap(self, unicode resource, double capval=1):
        cdef int res_index = self._res_dict[resource]
        cdef int u, v, e
        cdef ndarray vars
        for e in arange(self._load_array.shape[5]):
            vars = self._xps[:, :, e].reshape(-1)
            print (numpy.may_share_memory(vars, self._xps))
            # print (len(vars))
            ind = vars.nonzero()
            # print (len(ind[0]))
            for u in arange(self._load_array.shape[1]):
                for v in arange(self._load_array.shape[2]):
                    coeffs = \
                        self._load_array[res_index, u, v, :, :, e].reshape(-1)
                    expr = LinExpr(coeffs[ind], vars[ind])
                    self.opt.addConstr(expr <= capval)
        self.opt.update()


                    # for resource in self._load_dict:
                    #     for nodeorlink in self._load_dict[resource]:
                    #         for e in self._load_dict[resource][nodeorlink]:
                    #             expr = LinExpr()
                    #             for tc in self._load_dict[resource][nodeorlink][e]:
                    #                 expr.addTerms(itervalues(self._load_dict[resource][nodeorlink][e][
                    #                                   tc]),
                    #                               iterkeys(self._load_dict[resource][nodeorlink][e][
                    #                                   tc]))
                    #             self.opt.addConstr(expr <= capval)

                    # old version
                    # if resource_name not in self.expr:
                    #     self.expr[resource_name] = {}
                    # for node in node_caps:
                    #     if node not in self.expr[resource_name]:
                    #         self.expr[resource_name][node] = [None] * num_epochs
                    # for link in link_caps:
                    #     if link not in self.expr[resource_name]:
                    #         self.expr[resource_name][link] = [None] * num_epochs
                    #
                    # cdef unicode prefix, name
                    # for tc in pptc:
                    #     for path in pptc[tc]:
                    #         for node in path.nodes():
                    #             if node in node_caps and path.uses_box(node):
                    #                 prefix = u'NodeLoad_{}_{}'.format(resource_name, node)
                    #                 self._consume_helper(tc, path, node, num_epochs,
                    #                                      prefix, resource_name, cost,
                    #                                      node_caps)
                    #
                    #         for link in path.links():
                    #             if link in link_caps:
                    #                 prefix = u'LinkLoad_{}_{}'.format(resource_name,
                    #                                                  tup2str(link))
                    #                 self._consume_helper(tc, path, link, num_epochs,
                    #                                      prefix, resource_name,
                    #                                      cost, link_caps)

    cpdef consume_per_path(self, pptc, unicode resource_name, double cost,
                           node_caps, link_caps):
        raise NotImplemented

    cdef _req_all(self, pptc, traffic_classes=None, req_type=None):
        self._disable_paths(pptc)
        if req_type is None:
            raise SOLException(u'A type of constraint is needed for reqAll()')
        cdef int pi
        if traffic_classes is None:
            traffic_classes = pptc.keys()
        if req_type.lower() == u'node':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    for n in path:
                        self.opt.addConstr(self.v(bp(tc, pi)) <= self.v(bn(n)))
        elif req_type.lower() == u'edge' or req_type.lower == u'link':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    # TODO: see if this can be optimized
                    for link in path.links():
                        self.opt.addConstr(
                            self.v(bp(tc, pi)) <= self.v(be(*link)))
        else:
            raise SOLException(u'Unknown type of constraint for reqAll()')
        self.opt.update()

    cdef _req_some(self, pptc, traffic_classes=None, req_type=None):
        self._disable_paths(pptc)
        if req_type is None:
            raise SOLException(u'A type of constraint is needed for reqSome()')
        cdef int pi
        if traffic_classes is None:
            traffic_classes = iterkeys(pptc.keys)
        if req_type.lower() == u'node':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    expr = LinExpr()
                    for n in path:
                        expr.add(self.v(bn(n)))
                    self.opt.addConstr(self.v(bp(tc, pi)) <= expr)
        elif req_type.lower() == u'edge' or req_type.lower == u'link':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    expr = LinExpr()
                    # TODO: see if this can be optimized
                    for link in path.links():
                        expr.add(self.v(be(*link)))
                    self.opt.addConstr(self.v(bp(tc, pi)) <= expr)
        else:
            raise SOLException(u'Unknown type of constraint for reqSome()')
        self.opt.update()

    cpdef req_all_nodes(self, pptc, traffic_classes=None):
        return self.reqAll(pptc, traffic_classes, u'node')

    cpdef req_all_links(self, pptc, traffic_classes=None):
        return self._req_all(pptc, traffic_classes, u'link')

    cpdef req_some_nodes(self, pptc, traffic_classes=None):
        return self._req_some(pptc, traffic_classes, u'node')

    cpdef req_some_links(self, pptc, traffic_classes=None):
        return self._req_some(pptc, traffic_classes, u'link')

    cdef _disable_paths(self, pptc, traffic_classes=None):
        self._add_binary_vars(pptc, [u'path'])
        if traffic_classes is None:
            traffic_classes = iterkeys(pptc)
        cdef TrafficClass tc
        cdef Path path
        cdef int epoch
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        for tc in traffic_classes:
            for path in pptc[tc]:
                for epoch in range(num_epochs):
                    self.opt.addConstr(
                        self.v(xp(tc, path, epoch)) <= self.v(bp(tc, path)))
        self.opt.update()

    cpdef enforce_single_path(self, pptc, traffic_classes):
        self._disable_paths(pptc)
        if traffic_classes is None:
            traffic_classes = iterkeys(pptc)
        cdef int pi
        for tc in traffic_classes:
            for pi, path in enumerate(pptc[tc]):
                self.opt.addConstr(self.v(bp(tc, pi)))
        self.opt.update()

    cpdef cap_num_paths(self, pptc, int max_paths):
        self._disable_paths(pptc)
        # self.opt.addConstr(quicksum() <= max_paths)
        self.opt.addConstr(quicksum([v for v in self.opt.getVars() if
                                     v.varName.startswith(
                                         u'binpath')]) <= max_paths,
                           name=u'cap.paths')
        self.opt.update()

    cpdef min_latency(self, pptc, weight=1.0,
                      bool norm=True, epoch_mode=u'max', name=None):
        self._varindex[RES_LATENCY if name is None else name] = latency = \
            self.opt.addVar(name=RES_LATENCY if name is None else name)
        self._varindex[u'flip_{}'.format(name) \
            if name is None else RES_NOT_LATENCY] = notlatency = \
            self.opt.addVar(name=u'flip_{}'.format(name) \
                if name is None else RES_NOT_LATENCY,
                            obj=weight)
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef int epoch
        # cdef unicode name
        # for epoch in range(num_epochs):
        #     name = '{}_{}'.format(LATENCY, epoch)
        #     self._varindex[name] = sel.opt.addVar(name=name, lb=0, ub=None)
        self.opt.update()

        cdef double norm_factor = 1.0
        if norm:
            # norm_factor = sum(map(len, [paths for paths in itervalues(pptc)]))
            norm_factor = 1.0 * self.topo.diameter() * self.topo.num_nodes() \
                          * self.topo.num_nodes()

        if epoch_mode == u'max':
            for epoch in range(num_epochs):
                latency_expr = LinExpr()
                for tc in pptc:
                    for path in pptc[tc]:
                        latency_expr.addTerms(len(path), self.v(xp(tc, path,
                                                                   epoch)))

                self.opt.addConstr(latency >= latency_expr / norm_factor)
        elif epoch_mode == u'sum':
            latency_expr = LinExpr()
            for epoch in range(num_epochs):
                for tc in pptc:
                    for path in pptc[tc]:
                        latency_expr.addTerms(len(path), self.v(xp(tc, path,
                                                                   epoch)))
            self.opt.addConstr(latency >= latency_expr / norm_factor)
        else:
            raise ValueError(u'Unknown epoch_mode')
        self.opt.addConstr(notlatency == 1 - latency)
        self.opt.update()
        return notlatency

    cpdef node_budget(self, budgetFunc, int bound):
        """
        Enable at most *bound* nodes
        :param topology:
        :param budgetFunc:
        :param bound:
        :return:
        """
        self._add_binary_vars(None, [u'node'])
        expr = LinExpr()
        for n in self.topo.nodes(data=False):
            expr.add(self.v(bn(n)), budgetFunc(n))
        self.opt.addConstr(expr <= bound)
        self.opt.update()

    cdef _min_load(self, unicode resource, tcs, unicode prefix, weight,
                   epoch_mode, name):
        # this is the overall objective
        # objname = u'Max{}_{}'.format(prefix, resource)
        objname = name
        flipobjname = u'MinSpare{}_{}'.format(prefix, resource)
        self._varindex[objname] = obj = self.opt.addVar(name=objname)
        self._varindex[flipobjname] = \
            flipobj = self.opt.addVar(name=flipobjname, obj=weight)
        self.opt.update()

        # this will create variables for objective within each epoch
        cdef int num_epochs = ma.compressed(tcs[0].volFlows).size
        cdef int e
        cdef unicode name2
        per_epoch_objs = [None] * num_epochs
        for e in range(num_epochs):
            name2 = u'{}_{}'.format(objname, e)
            self._varindex[name] = per_epoch_objs[e] = \
                self.opt.addVar(lb=0, name=name)
        self.opt.update()

        cdef int res_index = self._res_dict[resource]
        cdef int u, v, tcid, pathid
        cdef ndarray tc_inds = array([tc.ID for tc in tcs])
        for u in range(self._load_array.shape[1]):
            for v in range(self._load_array.shape[2]):
                for e in range(self._load_array.shape[5]):

                    vars = self._xps[tc_inds, :, e]
                    ind = vars.nonzero()
                    coeffs = self._load_array[res_index, u, v, tc_inds, :, e]
                    expr = LinExpr(coeffs[ind], vars[ind])
                    # for tcid in self._load_array.axis[4]:
                    #     for pathid in self._load_array.axis[5]:
                    #         expr.add(self._xps[tcid][pathid][e],
                    #                  self._load_array[
                    #                      res_index, u, v, e, tcid, pathid])
                    self.opt.addConstr(expr <= per_epoch_objs[e])

        # within each epoch, set per-epoch objective to be the max across
        # links/nodes for given traffic classes:
        # for resource in self._load_dict:
        #     for nodeorlink in self._load_dict[resource]:
        #         for e in self._load_dict[resource][nodeorlink]:
        #             expr = LinExpr()
        #             for tc in self._load_dict[resource][nodeorlink][e]:
        #                 if tc in tcs:
        #                     expr.addTerms(
        #                         self._load_dict[resource][nodeorlink][e][
        #                             tc].values(),
        #                         self._load_dict[resource][nodeorlink][e][
        #                             tc].keys())
        #             self.opt.addConstr(expr <= per_epoch_objs[e])


        # Now set the global objective based on per-epoch objectives.
        # There are two possible modes: 'max' and 'sum'
        if epoch_mode == u'max':
            for e in range(num_epochs):
                self.opt.addConstr(obj >= per_epoch_objs[e])
        elif epoch_mode == u'sum':
            self.opt.addConstr(obj >= quicksum(per_epoch_objs))
        else:
            raise ValueError(u'Unkown epoch_mode objective mode composition')

        # flipped objective is just 1 - real objective
        self.opt.addConstr(flipobj == 1 - obj)
        # Model update
        self.opt.update()
        return flipobj  # Return global obj variable (for this resource/prefix)

    cpdef min_node_load(self, unicode resource, tcs, weight=1.0,
                        epoch_mode=u'max', name=None):
        """
        Minimize node load for a particular resource
        :param resource:
        :param tcs:
        :param weight:
        :param epoch_mode:
        :return:
        """
        return self._min_load(resource, tcs, u'NodeLoad', weight, epoch_mode,
                              name)

    cpdef min_link_load(self, unicode resource, tcs, weight=1.0,
                        epoch_mode=u'max', name=None):
        return self._min_load(resource, tcs, u'LinkLoad', weight, epoch_mode,
                              name)

    cpdef max_flow(self, pptc, weight=1.0, name=None):
        self._varindex[OBJ_MAX_ALL_FLOW if name is None else name] = obj = \
            self.opt.addVar(name=OBJ_MAX_ALL_FLOW if name is None else name,
                            obj=weight, lb=0, ub=1)
        self.opt.update()
        self.opt.addConstr(
            obj == quicksum([self.v(al(tc)) for tc in pptc]) / len(pptc))
        self.opt.update()
        return obj

    cpdef max_min_flow(self, pptc, weight=1.0, name=None):
        self._varindex[MAX_MIN_FLOW] = obj = \
            self.opt.addVar(name=MAX_MIN_FLOW if name is None else name,
                            obj=weight, lb=0)
        self.opt.update()
        for tc in pptc:
            self.opt.addConstr(obj >= self.v(al(tc)))
        self.opt.update()
        return obj

    cdef _get_load(self, unicode resource, unicode prefix, bool value=True):
        # logger.debug("loadstring: Max{}_{}".format(prefix, resource))
        v = self.v("Max{}_{}".format(prefix, resource))
        return v.x if value else v

    cpdef get_max_link_load(self, unicode resource, bool value=True):
        return self._get_load(resource, u'LinkLoad', value)

    cpdef get_max_node_load(self, unicode resource, bool value=True):
        return self._get_load(resource, u'NodeLoad', value)

    cpdef get_latency(self, bool value=True):
        """
        Return the latency objective value
        :param value:
        :return:
        """
        v = self.v(RES_LATENCY)
        # logger.debug("Latency is %f" % v.x)
        return v.x if value else v

    cpdef get_maxflow(self, bool value=True):
        v = self.v(OBJ_MAX_ALL_FLOW)
        return v.x if value else v

    cpdef relax_to_lp(self):
        """
        Change integer (or binary) variables to continuous variables.

        .. warning::

            Solution is no longer guaranteed to be optimal (or even to make sense).
            This assumes you know what you are doing and are intentionally attempting to
            implement randomized rounding or other similar techniques.
        """
        for v in self.opt.getVars():
            if v.vType == GRB.BINARY:
                self.intvars.add(v)
                v.vType = GRB.CONTINUOUS
        self.opt.update()

    cpdef set_time_limit(self, long time):
        """
        Limit how long Gurobi looks for the solution.
        :param time: time, in milliseconds
        :return:
        """
        self.opt.params.TimeLimit = time
        self.opt.update()

    # cdef _dump_expressions(self):
    #     cdef unicode resource_name, name, prefix
    #     cdef int epoch  #, num_epochs
    #     v = None
    #     # num_epochs = len(next(itervalues(next(itervalues(self.expressions)))))
    #     for resource_name in self.expr:
    #         for node_or_link in self.expr[resource_name]:
    #             if isinstance(node_or_link, tuple):
    #                 prefix = u'LinkLoad_{}_{}'.format(resource_name,
    #                                                  tup2str(node_or_link))
    #             else:
    #                 prefix = u'NodeLoad_{}_{}'.format(resource_name,
    #                                                  node_or_link)
    #             for epoch, expr in enumerate(
    #                     self.expr[resource_name][node_or_link]):
    #                 if expr is not None:
    #                     name = '{}_{}'.format(prefix, epoch)
    #                     v = self.v(name)
    #                     self.opt.addConstr(expr == v)
    #     self.opt.update()
    #     self.expr = {}

    cpdef solve(self):
        """
        Solve the optimization
        """
        start = time.time()
        # logger.debug(start)
        self.opt.optimize()
        if self._do_time:
            # logger.debug(time.time())
            self._time = time.time() - start
            # logger.debug(u'Time to solve: %f', self._time)

    cpdef write(self, unicode fname):
        """
        Writes the LP/ILP formulation to disk.
        ".lp" suffix is appended automatically

        :param fname: filename of the lp file
        """
        self.opt.write("{}.lp".format(fname))

    cpdef write_solution(self, unicode fname):
        """
        Write the solution to disk

        :param fname: filename of the solution file.
            ".sol" suffix is appended automatically
        """
        # logger.debug("{}.sol".format(fname))
        self.opt.write("{}.sol".format(fname))

    def get_gurobi_model(self):
        """
        Returns the underlying Gurobi model
        """
        return self.opt

    cpdef get_vars(self):
        return [v.VarName for v in self.opt.getVars()]

    cpdef get_var_values(self):
        """
        Returns the mapping of variable names to values assigned by optimization
        """
        return {var.VarName: var.x for var in self.opt.getVars()}

    cdef bool _has_var(self, unicode varname):
        return varname in self._varindex

    def copy(self):
        """
        Create a copy of the optimization
        :return:
        """
        raise NotImplemented
        # FIXME: should this be implemented? ¯\_(ツ)_/¯
        c = OptimizationGurobi(self.topo)
        c.opt = self.opt.copy()
        c.expressions = copy.copy(self.expr)
        c._varindex = copy.copy(self._varindex)
        return c

    def __copy__(self):
        # Technically, this shouldn't be raised. haha. ¯\_(ツ)_/¯
        # FIXME: don't write shitty code
        raise NotImplemented

    cpdef get_solved_objective(self):
        """
        :return: The objective value after the optimization is solved
        """
        return self.opt.ObjVal

    cpdef is_solved(self):
        """
        Check if the optimization is solved

        :return:
        """
        # TODO: does this have other status codes for MIP, like cplex?
        return self.opt.Status == GRB.OPTIMAL

    cpdef v(self, unicode varname):
        """
        Return variable by name

        :param varname:
        :return:
        """
        return self._varindex[varname]

    cpdef get_path_fractions(self, pptc, bool flow_carrying_only=True):
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef int e = 0
        result = {}
        for e in range(num_epochs):
            result[e] = {}
            for tc, paths in iteritems(pptc):
                result[e][tc] = []
                for path in paths:
                    newpath = copy.copy(path)
                    newpath.set_flow_fraction(
                        self.opt.getVarByName(xp(tc, path, e)).x)
                    if newpath.flow_fraction() > 0 and flow_carrying_only:
                        result[e][tc].append(newpath)
                    elif not flow_carrying_only:
                        result[e][tc].append(newpath)
        return result

    cpdef get_chosen_paths(self, pptc):
        result = {}
        ii = {}  # inverse index of traffic class IDs to traffic classes
        iip = {}  # inverse index of traffic class IDs to path IDs to paths
        cdef TrafficClass tc
        cdef Path p
        # Build the indecies
        for tc in pptc:
            result[tc] = []
            ii[tc.ID] = tc
            iip[tc.ID] = {}
            for p in pptc[tc]:
                iip[tc.ID][p.get_id()] = p
        # Go through the variables and pick our paths.
        cdef int tcid, pid
        for v in self.opt.getVars():
            # Look only on binary path variables
            if v.varName.startswith(u'binpath'):
                l = v.varName.split(u'_')
                tcid = int(l[1])
                pid = int(l[2])
                if v.x > 0:  # Was picked
                    result[ii[tcid]].append(iip[tcid][pid])
        return result

    cpdef fix_paths(self, pptc):
        """
        Fix flow allocation of for given paths to a precise value.

        :param pptc: path per traffic class, with flow fractions set
        """
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        for tc in pptc:
            for p in pptc[tc]:
                for e in range(num_epochs):
                    self.opt.addConstr(self.v(xp(tc, p, e)) == \
                                       p.flow_fraction())
        self.opt.update()

    cpdef double get_time(self):
        """
        :return: The time it took to solve the optimization
        """
        return self._time

    cpdef get_xps(self):
        return self._xps

    cpdef get_fractions(self):
        return _get_path_load(self._xps)

# def _extract_x(v):
#     try:
#         return v.x
#     except AttributeError:
#         return 0

# _get_path_load = frompyfunc(_extract_x, 1, 1)

cdef add_named_constraints(opt, app):
    for c in app.constraints:
        if c == ALLOCATE_FLOW:
            opt.allocate_flow(app.pptc)
        elif c == ROUTE_ALL:
            opt.route_all(app.pptc)
        elif c[0] == CAP_LINKS:
            opt.capLinks(app.pptc, *c[1:])
        elif c[0] == CAP_NODES:
            opt.capNodes(app.pptc, *c[1:])
        elif c == OBJ_MAX_ALL_FLOW:
            opt.max_flow(app.pptc)
        else:
            raise InvalidConfigException("Unsupported constraint type")

cpdef add_obj_var(app, opt, weight=0, epoch_mode=u'max'):
    """
    Add the objective value of given application to the optimization

    :param app: the application
    :param topo:
    :param opt:
    :param weight:
    :param resource:
    :return:
    """
    assert (epoch_mode == u'max' or epoch_mode == u'sum')
    cdef unicode ao, res, aol
    if isinstance(app.obj, tuple):
        ao = app.obj[0]
        res = app.obj[1]
    else:
        ao = app.obj
    aol = ao.lower()  # App objective lower -- aol
    if aol == OBJ_MIN_LINK_LOAD:
        return opt.min_link_load(res, app.objTC, weight, epoch_mode,
                                 name=app.name)
    elif aol == OBJ_MIN_LATENCY:
        return opt.min_latency({tc: app.pptc[tc] for tc in app.objTC},
                               weight, epoch_mode=epoch_mode,
                               name=app.name)
    elif aol == MIN_NODE_LOAD:
        return opt.min_node_load(res, app.objTC, weight, epoch_mode,
                                 name=app.name)
    elif aol == OBJ_MAX_ALL_FLOW:
        return opt.max_flow(app.pptc, weight, name=app.name)
    else:
        raise InvalidConfigException("Unknown objective")

cpdef get_obj_var(app, opt):
    """
    Return the objective value for the given application, after the
    optimization has been solved

    :param app: The application
    :param opt: Solved optimization
    :return:
    """
    return opt.v(app.name).x
    # cdef unicode ao, res, aol
    # if isinstance(app.obj, tuple):
    #     ao = app.obj[0]
    #     res = app.obj[1]
    # else:
    #     ao = app.obj
    # aol = ao.lower()  # App objective lower -- aol
    # if aol == MIN_LINK_LOAD:
    #     return opt.get_max_link_load(res)
    # elif aol == MIN_LATENCY:
    #     return opt.get_latency()
    # elif aol == MIN_NODE_LOAD:
    #     return opt.get_max_node_load(res)
    # elif aol == MAX_ALL_FLOW:
    #     return opt.get_maxflow()
    # else:
    #     raise InvalidConfigException("Unknown objective")
