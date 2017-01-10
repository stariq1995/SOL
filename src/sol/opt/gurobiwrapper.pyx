# coding=utf-8
# cython: profile=True
# distutils: define_macros=CYTHON_TRACE_NOGIL=1
"""
Wrapper around Gurobi
"""

from __future__ import division, print_function

import sys

from sol.utils.const import ERR_NO_GUROBI

try:
    if sys.version_info >= (3, 5):
        from gurobi import *
    else:
        from gurobipy import *
except ImportError as e:
    print(ERR_NO_GUROBI)
    raise e

import time

from numpy import ma, zeros, ones, arange, array, empty, not_equal
from six import iterkeys, next
from six.moves import range
from cpython cimport bool
from sol.utils.exceptions import SOLException, InvalidConfigException
from sol.path.paths cimport Path, PPTC, PathWithMbox
from sol.topology.traffic cimport TrafficClass
from sol.topology.topologynx cimport Topology
from sol.utils.const import RES_LATENCY, OBJ_MAX_ALL_FLOW, ALLOCATE_FLOW, \
    CAP_LINKS, \
    CAP_NODES, OBJ_MIN_LINK_LOAD, OBJ_MIN_LATENCY, MIN_NODE_LOAD, ROUTE_ALL, \
    RES_NOT_LATENCY
from sol.utils.logger import logger
from collections import defaultdict
from sol.opt.varnames import be, bn, bp, xp

OBJ_MAX_LINK_SPARE_CAP = u'maxlinkspare'
OBJ_MAX_NODE_SPARE_CAP = u'maxnodespare'
OBJ_MAX_NOT_LATENCY = u'maxnotlatency'

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:
    """
    Represents a SOL optimization problem.
    Uses Gurobi for building and solving the model.
    """
    def __init__(self, Topology topo, PPTC all_pptc, bool measure_time=True):
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
        self._all_pptc = all_pptc
        res_set = set()

        # self._res_mapping = defaultdict(lambda: [])
        for node in topo.nodes():
            rl = topo.get_resources(node)
            res_set.update(rl)
        #     for r in rl:
        #         self._res_mapping[r].append((node, node))
        #
        for link in topo.links():
            rl = topo.get_resources(link)
            res_set.update(rl)
        #     for r in rl:
        #         self._res_mapping[r].append(link)
        #
        # self._res_dict = {r: i for i, r in enumerate(res_set)}
        if len(set([ma.compressed(x.volFlows).size for x in
                    all_pptc.tcs()])) != 1:
            raise ValueError(
                'Number of epochs is inconsistent across traffic classes')
        self.num_epochs = ma.compressed(next(all_pptc.tcs()).volFlows).size
        cdef int max_paths = all_pptc.max_paths()
        self._max_paths = max_paths
        # logger.debug("maxpaths: %d" % max_paths)
        self._xps = empty(shape=(all_pptc.num_tcs(), max_paths, self.num_epochs),
                          dtype=object)
        self._xps.fill(None)
        self._als = zeros((all_pptc.num_tcs(), self.num_epochs), dtype=object)
        self._bps = zeros((all_pptc.num_tcs(), max_paths), dtype=object)
        self._bns = zeros(topo.num_nodes())
        self._bes = zeros((topo.num_nodes(), topo.num_nodes()))
        # self._load_array = zeros((len(res_set), topo.num_nodes(),
        #                           topo.num_nodes(),
        #                           all_pptc.num_tcs(), max_paths,
        #                           self.num_epochs))
        self._load_dict = {}
        for res in res_set:
            self._load_dict[res] = {}
            for n in topo.nodes():
                self._load_dict[res][n] = None

            for l in topo.links():
                self._load_dict[res][l] = None
                # zeros((all_pptc.num_tcs(), max_paths,
                #                              self.num_epochs))
        self._add_decision_vars()

        logger.debug("Initialized Gurobi wrapper")

    cdef _add_decision_vars(self):
        """
        Add desicision variables of the form x_* responsible for determining
        the amount of flow on each path for each TraffiClass (in each epoch).
        """
        cdef TrafficClass tc
        cdef int epoch, pathid
        for tc in self._all_pptc:
            for pathid in arange(self._all_pptc.num_paths(tc)):
                for epoch in arange(self.num_epochs):
                    self._xps[tc.ID, pathid, epoch] = \
                        self.opt.addVar(lb=0, ub=1, name='x_{}_{}_{}'.format(tc.ID, pathid, epoch))

        self.opt.update()
        logger.debug("Added desicion vars")

    cdef _add_binary_vars(self, PPTC pptc, vtypes):
        # cdef unicode name
        cdef int pi
        # cdef Path p
        cdef bool mod = False
        for t in vtypes:
            if t.lower() == u'node':
                for n in self.topo.nodes(False):
                    if isinstance(self._bns[n], float):
                        self._bns[n] = self.opt.addVar(vtype=GRB.BINARY, name=bn(n))
                        mod = True
            elif t.lower() == u'edge':
                for u, v in self.topo.links(False):
                    if isinstance(self._bes[u, v], float):
                        self._bes[u, v] = self.opt.addVar(vtype=GRB.BINARY, name=be(u,v))
                        mod = True
            elif t.lower() == u'path':
                for tc in pptc.tcs():
                    for pi in arange(pptc.num_paths(tc)):
                        if not isinstance(self._bps[tc.ID, pi], Var):
                            self._bps[tc.ID, pi] = \
                                self.opt.addVar(vtype=GRB.BINARY,
                                                name='bp_{}_{}'.format(tc.ID,
                                                                       pi))
                            mod = True
            else:
                raise SOLException("Unknown binary variable type")
        if mod:
            self.opt.update()

    cpdef allocate_flow(self, tcs, allocation=None):
        """
        Allocate network flow for each traffic class by allocating flow on each
        path (and summing it up for each traffic class)

        :param tcs: traffic classes
        :param allocation: if given, allocation for given traffic classes will
            be set to this value. Allocation must be between 0 and 1
        :raises: ValueError if the given allocation is not between 0 and 1
        """
        cdef int pi, epoch
        cdef TrafficClass tc
        for tc in tcs:
            for epoch in range(self.num_epochs):
                self._als[tc.ID, epoch] = v = self.opt.addVar(lb=0, ub=1,
                                                              name='a_{}_{}'.format(
                                                                  tc.ID, epoch))
                # create an empty expression
                lhs = LinExpr()
                # get only variables for existing paths
                ind = not_equal(self._xps[tc.ID, :, epoch], None).nonzero()
                vars = self._xps[tc.ID, :, epoch][ind]
                # construct the expression: sum up all varibles per traffic class
                lhs.addTerms(ones(vars.size),
                             vars)
                self.opt.addConstr(lhs == v, name='al_{}'.format(tc.ID))
                # If we also have an allocation value, add that constraint as well
                if allocation is not None:
                    self.opt.addConstr(v == allocation,
                                       name='al_{}'.format(tc.ID))
        self.opt.update()

    cpdef route_all(self, tcs):
        """
        Ensure that all available traffic is routed (no drops)
        by forcing the allocation of flow to be 1
        for all of the given traffic classes.

        :param tcs: list of traffic classes
        """
        cdef TrafficClass tc
        cdef int epoch
        for tc in tcs:
            for epoch in range(self.num_epochs):
                # This is sufficient as it forces both lower and upper bounds
                # on a variable to be 1
                self._als[tc.ID, epoch].lb = 1
        self.opt.update()

    cpdef consume(self, tcs, unicode resource, double cost, node_caps,
                  link_caps):
        """
        Compute the loads on a given resource by given traffic classes

        :param tcs: paths per traffic class
        :param resource: resource to be consumed
        :param cost: cost per flow for this resource
        """
        logger.debug(u'Consume: %s' % resource)
        cdef int e, pathid
        # cdef int res_index = self._res_dict[resource]

        for tc in tcs:
            vols = tc.volFlows.compressed()
            for pathid, path in enumerate(self._all_pptc.paths(tc)):
                if isinstance(path, PathWithMbox):
                    for node in path.useMBoxes:
                        if node in node_caps:
                            if self._load_dict[resource][node] is None:
                                self._load_dict[resource][node] = zeros((self._all_pptc.num_tcs(),
                                                                         self._max_paths, self.num_epochs))
                            self._load_dict[resource][node][tc.ID, pathid, :] = vols * cost/ node_caps[node]
                            # self._load_array[res_index, node, node, tc.ID, pathid, :] = \
                            #     vols * cost / node_caps[node]

                for link in path.links():
                    if link in link_caps:
                        if self._load_dict[resource][link] is None:
                            self._load_dict[resource][link] = zeros((self._all_pptc.num_tcs(),
                                                                     self._max_paths, self.num_epochs))
                        self._load_dict[resource][link][tc.ID, pathid, :] = vols * cost/ link_caps[link]
                        # self._load_array[res_index, u, v, tc.ID, pathid, :] = \
                        #     vols * cost / link_caps[link]

    cpdef cap(self, unicode resource, tcs=None, double capval=1):
        """ Cap the usage of a given resource with a given value

        :param resource: the name of resource to cap
        :param capval: the maximum utilization of given resource
        """
        # Sanity check on cap value
        if not 0 <= capval <= 1:
            raise ValueError("Cap value must be between 0 and 1")
        # cdef int res_index = self._res_dict[resource]
        cdef int u, v, e
        cdef ndarray vars

        if tcs is None:
            tcs = self._all_pptc.tcs()
        tcind = [tc.ID for tc in tcs]
        for e in arange(self.num_epochs):
            vars = self._xps[tcind, :, e]
            ind = not_equal(None, vars).nonzero()
            # for u, v in self._res_mapping[resource]:
            for node_or_link in self._load_dict[resource]:
                if self._load_dict[resource][node_or_link] is None:
                    continue
                coeffs = self._load_dict[resource][node_or_link][tcind,:,e]
                # coeffs = \
                #     self._load_array[res_index, u, v, :, :, e].reshape(-1)
                expr = LinExpr(coeffs[ind], vars[ind])
                self.opt.addConstr(expr <= capval,
                                   name='cap.{}.{}.{}'.format(resource,
                                                              str(node_or_link), e))
        self.opt.update()

    cpdef consume_per_path(self, pptc, unicode resource_name, double cost,
                           node_caps, link_caps):
        raise NotImplemented

    cdef _req_all(self, pptc, traffic_classes=None, req_type=None):
        raise NotImplemented
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
        raise NotImplemented
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

    cdef _disable_paths(self, PPTC pptc, traffic_classes=None):
        self._add_binary_vars(pptc, [u'path'])
        if traffic_classes is None:
            traffic_classes = pptc.tcs()
        cdef TrafficClass tc
        cdef Path path
        cdef int epoch
        for tc in traffic_classes:
            for pi, path in enumerate(pptc[tc]):
                for epoch in range(self.num_epochs):
                    self.opt.addConstr(
                        self._xps[tc.ID, pi, epoch] <= self._bps[tc.ID, pi],
                        name='dispath')
        self.opt.update()

    cpdef enforce_single_path(self, pptc, traffic_classes):
        self._disable_paths(pptc)
        if traffic_classes is None:
            traffic_classes = pptc.tcs()
        cdef int pi
        for tc in traffic_classes:
            for pi, path in enumerate(pptc[tc]):
                self.opt.addConstr(self.v(bp(tc, pi)))
        self.opt.update()

    cpdef cap_num_paths(self, int max_paths, PPTC pptc=PPTC()):
        if pptc.empty():
            pptc = self._all_pptc
        self._disable_paths(pptc)
        # self.opt.addConstr(quicksum() <= max_paths)
        self.opt.addConstr(quicksum(self._bps.reshape(-1)) <= max_paths,
                           name='path_cap')
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
        cdef int epoch, pi

        cdef double norm_factor = 1.0
        if norm:
            # norm_factor = sum(map(len, [paths for paths in itervalues(pptc)]))
            norm_factor = 1.0 * self.topo.diameter() * self.topo.num_nodes() \
                          * self.topo.num_nodes()

        if epoch_mode == u'max':
            for epoch in range(self.num_epochs):
                latency_expr = LinExpr()
                for tc in pptc:
                    for pi, path in enumerate(pptc[tc]):
                        latency_expr.addTerms(len(path),
                                              self._xps[tc.ID, pi, epoch])

                self.opt.addConstr(latency >= latency_expr / norm_factor)
        elif epoch_mode == u'sum':
            latency_expr = LinExpr()
            for epoch in range(self.num_epochs):
                for tc in pptc:
                    for pi, path in enumerate(pptc[tc]):
                        latency_expr.addTerms(len(path),
                                              self._xps[tc.ID, pi, epoch])
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
        obj = self.opt.addVar(name=objname, lb=0)
        flipobj = self.opt.addVar(name=flipobjname, obj=weight)
        self.opt.update()

        # this will create variables for objective within each epoch
        cdef int e
        cdef unicode per_epoch_name
        per_epoch_objs = [None] * self.num_epochs
        for e in range(self.num_epochs):
            per_epoch_name = u'{}_{}'.format(objname, e)
            per_epoch_objs[e] = self.opt.addVar(lb=0, name=per_epoch_name)
        self.opt.update()

        cdef int tcid, pathid
        cdef ndarray tc_inds = array([tc.ID for tc in tcs])

        for e in range(self.num_epochs):
            vars = self._xps[tc_inds, :, e]
            ind = not_equal(None, vars).nonzero()
            for node_or_link in self._load_dict[resource]:
                if self._load_dict[resource][node_or_link] is None:
                    continue
                coeffs = self._load_dict[resource][node_or_link][tc_inds, : , e]
                expr = LinExpr(coeffs[ind], vars[ind])
                self.opt.addConstr(expr <= per_epoch_objs[e],
                                   name='ml_{}_{}'.format(str(node_or_link), e))

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
            for e in range(self.num_epochs):
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
        for e in range(self.num_epochs):
            self.opt.addConstr(
                obj == quicksum(
                    [self._als[tc.ID, e] for tc in pptc]) / pptc.num_tcs())
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

    cpdef solve(self):
        """
        Solve the optimization
        """
        start = time.time()
        self.opt.optimize()
        if self._do_time:
            self._time = time.time() - start

    cpdef write(self, fname):
        """
        Writes the LP/ILP formulation to disk.
        ".lp" suffix is appended automatically

        :param fname: filename of the lp file
        """
        self.opt.write("{}.lp".format(fname))

    cpdef write_solution(self, fname):
        """
        Write the solution to disk

        :param fname: filename of the solution file.
            ".sol" suffix is appended automatically
        """
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
        return self.opt.getVarByName(varname)

    cpdef get_xps(self):
        return self._xps

    cpdef get_paths(self, int epoch=0):
        """
        :param epoch:
        :return:
        """
        cdef TrafficClass tc
        cdef int pi
        cdef Path p
        cdef PPTC c = self._all_pptc.copy(deep=True)
        for tc in c.tcs():
            for pi, p in enumerate(c.paths(tc)):
                p.set_flow_fraction(self._xps[tc.ID, pi, epoch].x)
        return c

        # for e in range(num_epochs):
        #     result[e] = {}
        #     for tc, paths in iteritems(pptc):
        #         result[e][tc] = []
        #         for path in paths:
        #             newpath = copy.copy(path)
        #             newpath.set_flow_fraction(
        #                 self.opt.getVarByName(xp(tc, path, e)).x)
        #             if newpath.flow_fraction() > 0 and flow_carrying_only:
        #                 result[e][tc].append(newpath)
        #             elif not flow_carrying_only:
        #                 result[e][tc].append(newpath)
        # return result

    cpdef get_chosen_paths(self):
        # result = {}
        # ii = {}  # inverse index of traffic class IDs to traffic classes
        # iip = {}  # inverse index of traffic class IDs to path IDs to paths
        # cdef TrafficClass tc
        # cdef Path p
        # # Build the indecies
        # for tc in pptc:
        #     result[tc] = []
        #     ii[tc.ID] = tc
        #     iip[tc.ID] = {}
        #     for p in pptc[tc]:
        #         iip[tc.ID][p.get_id()] = p
        # Go through the variables and pick our paths.
        cdef TrafficClass tc
        cdef int pid
        for tc in self._all_pptc.tcs():
            ind = [x.x == 0 for x in
                   self._bps[tc.ID, :self._all_pptc.num_paths(tc)]]
            self._all_pptc.mask(tc, ind)
        # for v in self._bps:
        #
        #     # Look only on binary path variables
        #     if v.varName.startswith(u'binpath'):
        #         l = v.varName.split(u'_')
        #         tcid = int(l[1])
        #         pid = int(l[2])
        #         if v.x > 0:  # Was picked
        #             result[ii[tcid]].append(iip[tcid][pid])
        return self._all_pptc

    cpdef fix_paths(self, pptc):
        """
        Fix flow allocation of for given paths to a precise value.

        :param pptc: path per traffic class, with flow fractions set
        """
        cdef int pi
        for tc in pptc:
            for pi, p in enumerate(pptc[tc]):
                for e in range(self.num_epochs):
                    # Only fix non-zero paths
                    if p.flow_fraction() > 0:
                        self.opt.addConstr(self._xps[tc.ID, pi, e] == \
                                           p.flow_fraction())
        self.opt.update()

    cpdef double get_time(self):
        """
        :return: The time it took to solve the optimization
        """
        return self._time

    cpdef get_solution(self):
        vars = [dict(name=v.VarName, value=v.x) for v in self.opt.getVars()]
        # paths = []
        # for e in range(self.num_epochs):
        #     pptc = self.get_paths(e)
        #     for tc in pptc:
        #         for path in pptc.paths(tc):
        #             pd = dict(epoch=e)
        #             pd.update(path.encode())
        #             paths.append(pd)
        return dict(variables=vars)

cpdef add_named_constraints(opt, app):
    for c in app.constraints:
        res = None
        if isinstance(c, tuple):
            cl = c[0].lower()
            res = c[1]
        else:
            cl = c.lower()
        if cl == ALLOCATE_FLOW:
            opt.allocate_flow(app.pptc)
        elif cl == ROUTE_ALL:
            opt.route_all(app.pptc)
        elif cl == CAP_LINKS or cl == CAP_NODES:
            opt.cap(c[1], app.pptc, c[2])
        elif cl == OBJ_MAX_ALL_FLOW:
            opt.max_flow(app.pptc)
        else:
            raise InvalidConfigException("Unsupported constraint type %s" % c)

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
    res = None
    if isinstance(app.obj, tuple):
        ao = app.obj[0]
        res = app.obj[1]
    else:
        ao = app.obj
    aol = ao.lower()  # App objective lower -- aol
    if aol == OBJ_MIN_LINK_LOAD:
        if res is None:
            raise SOLException("A resource is required with this type of objective")
        return opt.min_link_load(res, app.objTC, weight, epoch_mode,
                                 name=app.name)
    elif aol == OBJ_MIN_LATENCY:
        return opt.min_latency({tc: app.pptc[tc] for tc in app.objTC},
                               weight, epoch_mode=epoch_mode,
                               name=app.name)
    elif aol == MIN_NODE_LOAD:
        if res is None:
            raise SOLException("A resource is required with this type of objective")
        return opt.min_node_load(res, app.objTC, weight, epoch_mode,
                                 name=app.name)
    elif aol == OBJ_MAX_ALL_FLOW:
        return opt.max_flow(app.pptc, weight, name=app.name)
    else:
        raise InvalidConfigException("Unknown objective %s" % ao)

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
