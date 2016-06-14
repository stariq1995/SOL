# coding=utf-8
from __future__ import division, print_function

try:
    # noinspection PyPackageRequirements
    from gurobipy import *
except ImportError as e:
    print("Cannot use Gurobi Python API. Please install Gurobi and gurobipy")
    raise e

import copy
import time

import numpy
cimport numpy
from numpy import ma
from six import iterkeys, itervalues, iteritems, next
from six.moves import range
from cpython cimport bool
from sol.utils.exceptions import SOLException
from sol.utils.pythonHelper cimport tup2str
from sol.path.paths cimport Path
from sol.topology.traffic cimport TrafficClass
from sol.topology.topologynx cimport Topology
from gurobiwrapper cimport OptimizationGurobi
from sol.opt.varnames cimport xp, al, bn, be, bp
from sol.opt.varnames import LATENCY, MAX_ALL_FLOW, ALLOCATE_FLOW, CAP_LINKS, \
    CAP_NODES, MIN_LINK_LOAD, MIN_LATENCY, MIN_NODE_LOAD, ROUTE_ALL
from sol.utils.logger import logger

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:
    """
    Represents a SOL optimization problem. Uses Gurobi for building the model and solving it.
    """
    def __init__(self, Topology topo, bool do_time=True):
        self.opt = Model()
        # self.opt.params.LogToConsole = 0
        self.expr = {}
        self.topo = topo
        self._varindex = {}
        self._do_time = do_time
        self._time = 0
        logger.debug("Init optimization")

    cpdef _add_decision_vars(self, dict pptc):
        cdef TrafficClass tc
        cdef Path path
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef int epoch = 0
        cdef str name
        cdef bool mod = False
        for tc in pptc:
            for path in pptc[tc]:
                for epoch in range(num_epochs):
                    name = xp(tc, path, epoch)
                    if not self._has_var(name):
                        self._varindex[name] = self.opt.addVar(lb=0, ub=1,
                                                               name=name)
                        mod = True
        if mod:
            self.opt.update()
        logger.debug("Added desicion vars")

    cdef _add_binary_vars(self, dict pptc, vtypes):
        cdef str name
        cdef Path p
        cdef bool mod = False
        for t in vtypes:
            if t.lower() == 'node':
                for n in self.topo.nodes(False):
                    name = bn(n)
                    if not self._has_var(name):
                        self._varindex[name] = self.opt.addVar(vtype=GRB.BINARY,
                                                               name=name)
                        mod = True
            elif t.lower() == 'edge':
                for u, v in self.topo.links(False):
                    name = be(u, v)
                    if not self._has_var(name):
                        self._varindex[name] = self.opt.addVar(vtype=GRB.BINARY,
                                                               name=name)
                        mod = True
            elif t.lower() == 'path':
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
        Allocate network flow
        :param pptc: paths per traffic class
        :param allocation: if given, allocation of given traffic classes will
            be set to this value.
        :return:
        """
        self._add_decision_vars(pptc)
        cdef int pi
        cdef int epoch = 0, num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef str name
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
                    for path in pptc[tc]:
                        lhs.addTerms(1, self.v(xp(tc, path, epoch)))
                    self.opt.addConstr(lhs == self.v(name))
        else:
            for tc in pptc:
                for epoch in range(num_epochs):
                    name = self.al(tc, epoch)
                    self.opt.addConstr(self.v(name) == allocation)
        self.opt.update()

    cpdef route_all(self, pptc):
        """
        Route all traffic for all traffic classes
        :param pptc:
        :return:
        """
        cdef int epoch = 0, num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef str name
        for tc in pptc:
            for epoch in range(num_epochs):
                name = al(tc)
                v = self.v(name)
                v.lb = v.ub = 1
        self.opt.update()

    # cpdef capLinks(self, pptc, resource, linkCaps, linkCapFunc):
    #     expressions = defaultdict(lambda: LinExpr())
    #     for tc in pptc:
    #         for path in pptc[tc]:
    #             for link in path.links():
    #                 expressions[link].addTerms(linkCapFunc(link, tc, path, resource),
    #                                            self.v(xp(tc, path)))
    #     for link, cap in linkCaps.iteritems():
    #         name = 'LinkLoad_{}_{}'.format(resource, tup2str(link))
    #         if self.v(name) is None:
    #             self.opt.addVar(name=name, ub=cap)
    #             self.opt.update()
    #         self.opt.addConstr(expressions[link] == self.v(name),
    #                            name='LinkCap.{}.{}'.format(resource,
    #                                                        tup2str(link)))
    #     self.opt.update()
    #
    # def capNodes(self, pptc, resource, nodeCaps, nodeCapFunc):
    #     cdef int pi
    #     expressions = defaultdict(lambda: LinExpr())
    #     for tc in pptc:
    #         for pi, path in enumerate(pptc[tc]):
    #             for node in path.nodes():
    #                 expressions[node].addTerms(nodeCapFunc(node, tc, path, resource),
    #                                            self.v(xp(tc, path)))
    #     for node, cap in nodeCaps.iteritems():
    #         name = 'NodeLoad_{}_{}'.format(resource, node)
    #         if self.v(name) is None:
    #             self.opt.addVar(name=name, ub=cap)
    #             self.opt.update()
    #         self.opt.addConstr(expressions[node] == self.v(name))
    #     self.opt.update()

    # TODO: consume & capNodes/Links are kind of redundant at this point, clean it up
    # TODO: write a separate TCAM function


    cdef _consume_helper(self, tc, path, node_or_link, int num_epochs,
                         str prefix, str resource_name, double cost, caps):
        cdef str name
        cdef int epoch
        for epoch in range(num_epochs):
            name = '{}_{}'.format(prefix, epoch)
            if not self._has_var(name):
                self._varindex[name] = self.opt.addVar(name=name, ub=1)
            v = self.v(xp(tc, path, epoch))
            if self.expr[resource_name][node_or_link][epoch] is None:
                self.expr[resource_name][node_or_link][epoch] = LinExpr()
            self.expr[resource_name][node_or_link][epoch].addTerms(
                tc.volFlows.compressed()[epoch] * cost / caps[node_or_link], v)
        self.opt.update()

    cpdef consume(self, pptc, str resource_name, double cost, node_caps,
                  link_caps):
        """
        :param pptc: paths per traffic class
        :param resource_name: resource to be consumed
        :param cost: cost per flow for this resource
        """
        logger.debug('Consume: %s' % resource_name)
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef int num_tcs = len(pptc)
        cdef int e
        if resource_name not in self.expr:
            self.expr[resource_name] = {}
        for node in node_caps:
            if node not in self.expr[resource_name]:
                self.expr[resource_name][node] = numpy.empty((num_epochs,
                                                             num_tcs))
        for link in link_caps:
            if link not in self.expr[resource_name]:
                self.expr[resource_name][link] = [None] * num_epochs

        cdef str prefix, name
        for tc in pptc:
            for path in pptc[tc]:
                for node in path.nodes():
                    if node in node_caps:
                        prefix = 'NodeLoad_{}_{}'.format(resource_name, node)
                        self._consume_helper(tc, path, node, num_epochs,
                                             prefix, resource_name, cost,
                                             node_caps)

                for link in path.links():
                    if link in link_caps:
                        if link not in self.expr[resource_name]:
                            self.expr[resource_name][link] = []
                        prefix = 'LinkLoad_{}_{}'.format(resource_name,
                                                         tup2str(link))
                        self._consume_helper(tc, path, link, num_epochs,
                                             prefix, resource_name,
                                             cost, link_caps)

    cdef _req_all(self, pptc, traffic_classes=None, req_type=None):
        self._disable_paths(pptc)
        if req_type is None:
            raise SOLException('A type of constraint is needed for reqAll()')
        cdef int pi
        if traffic_classes is None:
            traffic_classes = pptc.keys()
        if req_type.lower() == 'node':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    for n in path:
                        self.opt.addConstr(self.v(bp(tc, pi)) <= self.v(bn(n)))
        elif req_type.lower() == 'edge' or req_type.lower == 'link':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    # TODO: see if this can be optimized
                    for link in path.links():
                        self.opt.addConstr(
                            self.v(bp(tc, pi)) <= self.v(be(*link)))
        else:
            raise SOLException('Unknown type of constraint for reqAll()')
        self.opt.update()

    cdef _req_some(self, pptc, traffic_classes=None, req_type=None):
        self._disable_paths(pptc)
        if req_type is None:
            raise SOLException('A type of constraint is needed for reqSome()')
        cdef int pi
        if traffic_classes is None:
            traffic_classes = iterkeys(pptc.keys)
        if req_type.lower() == 'node':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    expr = LinExpr()
                    for n in path:
                        expr.add(self.v(bn(n)))
                    self.opt.addConstr(self.v(bp(tc, pi)) <= expr)
        elif req_type.lower() == 'edge' or req_type.lower == 'link':
            for tc in traffic_classes:
                for pi, path in enumerate(pptc[tc]):
                    expr = LinExpr()
                    # TODO: see if this can be optimized
                    for link in path.links():
                        expr.add(self.v(be(*link)))
                    self.opt.addConstr(self.v(bp(tc, pi)) <= expr)
        else:
            raise SOLException('Unknown type of constraint for reqSome()')
        self.opt.update()

    cpdef req_all_nodes(self, pptc, traffic_classes=None):
        return self.reqAll(pptc, traffic_classes, 'node')

    cpdef req_all_links(self, pptc, traffic_classes=None):
        return self._req_all(pptc, traffic_classes, 'link')

    cpdef req_some_nodes(self, pptc, traffic_classes=None):
        return self._req_some(pptc, traffic_classes, 'node')

    cpdef req_some_links(self, pptc, traffic_classes=None):
        return self._req_some(pptc, traffic_classes, 'link')

    cdef _disable_paths(self, pptc, traffic_classes=None):
        self._add_binary_vars(pptc, ['path'])
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
        self.opt.addConstr(quicksum([v for v in self.opt.getVars() if
                                     v.varName.startswith(
                                         'binpath')]) <= max_paths,
                           name='cap.paths')
        self.opt.update()

    cpdef min_latency(self, pptc, double weight=1.0,
                      bool norm=True, epoch_mode='max'):
        self._varindex[LATENCY] = latency = \
            self.opt.addVar(name=LATENCY, obj=weight)
        cdef int num_epochs = ma.compressed(next(iterkeys(pptc)).volFlows).size
        cdef int epoch
        # cdef str name
        # for epoch in range(num_epochs):
        #     name = '{}_{}'.format(LATENCY, epoch)
        #     self._varindex[name] = sel.opt.addVar(name=name, lb=0, ub=None)
        self.opt.update()

        cdef double norm_factor = 1.0
        if norm:
            # norm_factor = sum(map(len, [paths for paths in itervalues(pptc)]))
            norm_factor = self.topo.diameter() * self.topo.num_nodes() \
                          * self.topo.num_nodes()

        if epoch_mode=='max':
            for epoch in range(num_epochs):
                latency_expr = LinExpr()
                for tc in pptc:
                    for path in pptc[tc]:
                        latency_expr.addTerms(len(path), self.v(xp(tc, path,
                                                                   epoch)))

                    self.opt.addConstr(latency >= latency_expr / norm_factor)
        elif epoch_mode=='sum':
            self.opt.addConstr(latency >=
                               quicksum([self.v(xp(tc, path, epoch))
                                         for epoch in range(num_epochs)
                                         for tc in pptc
                                         for path in pptc[tc]]))
        self.opt.update()
        return latency

    cpdef node_budget(self, budgetFunc, int bound):
        """
        Enable at most *bound* nodes
        :param topology:
        :param budgetFunc:
        :param bound:
        :return:
        """
        self._add_binary_vars(None, ['node'])
        expr = LinExpr()
        for n in self.topo.nodes(data=False):
            expr.add(self.v(bn(n)), budgetFunc(n))
        self.opt.addConstr(expr <= bound)
        self.opt.update()

    # TODO: bring back mindiff
    # TODO: externalize strings

    cdef _min_load(self, str resource, str prefix, float weight, epoch_mode):
        logger.debug("In _min_load")
        objname = 'Max{}_{}'.format(prefix, resource)
        obj = self.opt.addVar(name=objname, obj=weight)
        self._varindex[objname] = obj
        self.opt.update()
        prefix = '{}_{}'.format(prefix, resource)
        if epoch_mode == 'max':
            for varname, var in iteritems(self._varindex):
                if varname.startswith(prefix):
                        self.opt.addConstr(obj >= var)
        elif epoch_mode == 'sum':
            self.opt.addConstr(obj >= quicksum([var for varname, var in
                                                iteritems(self._varindex)
                                                if varname.startswith(prefix)]))
        self.opt.update()
        return obj

    cpdef min_node_load(self, str resource, float weight=1.0, epoch_mode='max'):
        return self._min_load(resource, 'NodeLoad', weight, epoch_mode)

    cpdef min_link_load(self, str resource, float weight=1.0, epoch_mode='max'):
        return self._min_load(resource, 'LinkLoad', weight, epoch_mode)

    cpdef max_flow(self, pptc, double weight=1.0):
        self._varindex[MAX_ALL_FLOW] = obj = \
            self.opt.addVar(name=MAX_ALL_FLOW, obj=weight)
        self.opt.update()
        # 1-sum is required because we're keeping it a minimization problem
        self.opt.addConstr(obj == 1 - quicksum([self.v(al(tc)) for tc in pptc]))
        self.opt.update()

    cdef _get_load(self, str resource, str prefix, bool value=True):
        # logger.debug("loadstring: Max{}_{}".format(prefix, resource))
        v = self.v("Max{}_{}".format(prefix, resource))
        return v.x if value else v

    cpdef get_max_link_load(self, str resource, bool value=True):
        return self._get_load(resource, 'LinkLoad', value)

    cpdef get_max_node_load(self, str resource, bool value=True):
        return self._get_load(resource, 'NodeLoad', value)

    cpdef get_latency(self, value=True):
        """
        Return the latency objective value
        :param value:
        :return:
        """
        v = self.v(LATENCY)
        # logger.debug("Latency is %f" % v.x)
        return v.x if value else v

    cpdef relax_to_lp(self):
        """
        Change integer (or binary) variables to continuous variables.
        ..warning:
            Solution is no longer guaranteed to be optimal (or even make sense)
            This assumes you know what you're doing and are attempting to
            implement randomized rounding or something of that sort.
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

    cdef _dump_expressions(self):
        cdef str resource_name, name, prefix
        cdef int epoch, num_epochs
        v = None
        # num_epochs = len(next(itervalues(next(itervalues(self.expressions)))))
        for resource_name in self.expr:
            for node_or_link in self.expr[resource_name]:
                if isinstance(node_or_link, tuple):
                    prefix = 'LinkLoad_{}_{}'.format(resource_name,
                                                     tup2str(node_or_link))
                else:
                    prefix = 'NodeLoad_{}_{}'.format(resource_name,
                                                     node_or_link)
                for epoch, expr in enumerate(self.expr[resource_name][node_or_link]):

                    name = '{}_{}'.format(prefix, epoch)
                    v = self.v(name)
                    self.opt.addConstr(expr == v)
        self.opt.update()

    cpdef solve(self):
        """
        Solve the optimization
        """
        self._dump_expressions()
        start = time.time()
        # logger.debug(start)
        self.opt.optimize()
        if self._do_time:
            # logger.debug(time.time())
            self._time = time.time() - start
            # logger.debug('Time to solve: %f', self._time)

    cpdef write(self, str fname):
        """
        Writes the LP/ILP formulation to disk.
            ".lp" suffix is appended automatically
        :param fname: filename of the lp file
        """
        self.opt.write("{}.lp".format(fname))

    cpdef write_solution(self, str fname):
        """
        Write the solution to disk
        :param fname: filename of the solution file.
            ".sol" suffix is appended automatically
        """
        self.write("{}.sol".format(fname))

    def get_gurobi_model(self):
        """
        Returns the underlying Gurobi model
        """
        return self.opt

    cpdef get_var_values(self):
        """
        Returns the mapping of variable names to values assigned by optimization
        """
        return {var.VarName: var.x for var in self.opt.getVars()}

    cdef bool _has_var(self, str varname):
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

    cdef v(self, str varname):
        """
        Return variable by name
        :param varname:
        :return:
        """
        return self._varindex[varname]

    cpdef get_path_fractions(self, pptc, bool flow_carrying_only=True):
        # FIXME: this no longer works with epochs!!!
        result = {}
        for tc, paths in iteritems(pptc):
            result[tc] = []
            for path in paths:
                newpath = copy.copy(path)
                newpath.set_flow_fraction(self.opt.getVarByName(xp(tc, path)).x)
                if newpath.flow_fraction() > 0 and flow_carrying_only:
                    result[tc].append(newpath)
                elif not flow_carrying_only:
                    result[tc].append(newpath)
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
            if v.varName.startswith('binpath'):
                l = v.varName.split('_')
                tcid = int(l[1])
                pid = int(l[2])
                if v.x > 0:  # Was picked
                    result[ii[tcid]].append(iip[tcid][pid])
        return result

    # cpdef enable_timing(self):
    #     """
    #     Measure and store the time it took to solve the optimization
    #     :return:
    #     """
    #     self._do_time = True

    cpdef double get_time(self):
        """
        :return: The time it took to solve the optimization
        """
        return self._time

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
        else:
            raise InvalidConfigException("Unsupported constraint type")

cpdef add_obj_var(app, opt, double weight=0, epoch_mode='max'):
    """
    Add the objective value of given application to the optimization
    :param app: the application
    :param topo:
    :param opt:
    :param weight:
    :param resource:
    :return:
    """
    assert(epoch_mode == 'max' or epoch_mode == 'sum')
    cdef str ao, res, aol
    if isinstance(app.obj, tuple):
        ao = app.obj[0]
        res = app.obj[1]
    else:
        ao = app.obj
    aol = ao.lower()  # App objective lower -- aol
    if aol == MIN_LINK_LOAD:
        return opt.min_link_load(res, weight, epoch_mode)
    elif aol == MIN_LATENCY:
        return opt.min_latency({tc: app.pptc[tc] for tc in app.objTC},
                               weight, epoch_mode)
    elif aol == MIN_NODE_LOAD:
        return opt.min_node_load(res, weight, epoch_mode)
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
    cdef str ao, res, aol
    if isinstance(app.obj, tuple):
        ao = app.obj[0]
        res = app.obj[1]
    else:
        ao = app.obj
    aol = ao.lower()  # App objective lower -- aol
    if aol == MIN_LINK_LOAD:
        return opt.get_max_link_load(res)
    elif aol == MIN_LATENCY:
        return opt.get_latency()
    elif aol == MIN_NODE_LOAD:
        return opt.get_max_node_load(res)
    else:
        raise InvalidConfigException("Unknown objective")
