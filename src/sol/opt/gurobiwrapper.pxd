# coding=utf-8
from sol.path.paths cimport PPTC
from sol.topology.topologynx cimport Topology
from cpython cimport bool
from numpy cimport ndarray

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:

    # the gurobi model
    cdef public opt
    # topology
    cdef public Topology topo
    # time measurement vars
    cdef bool _do_time
    cdef double _time
    # load computation dict
    cdef public _load_dict
    # number of epochd
    cdef int num_epochs
    # all the gurobi var multi-dimensional arrays
    cdef ndarray _xps
    cdef ndarray _als
    cdef ndarray _bps
    cdef ndarray _bes
    cdef ndarray _bns
    # max number of paths in a single traffic class
    cdef int _max_paths
    # all the paths per traffic class
    cdef PPTC _all_pptc

    # internal variables and routing constraints
    cdef _add_decision_vars(self)
    cdef _add_binary_vars(self, PPTC pptc, vtypes)
    cdef _disable_paths(self, traffic_classes=*)
    cpdef allocate_flow(self, tcs, allocation=*)

    # Routing and path constraints
    cpdef route_all(self, tcs=*)
    cpdef cap_num_paths(self, int max_paths, PPTC pptc=*)
    cpdef enforce_single_path(self, traffic_classes)
    cpdef enforce_symmetric_paths(self, pptc)


    # resource consumption functions
    # cpdef consume(self, tcs, unicode resource, double cost, node_caps,
    #               link_caps, node_consume_mode=*, res_consume_mode=*)
    cpdef consume(self, tcs, unicode resource, cost_funcs, caps, mode)
    cpdef cap(self, unicode resource, caps, tcs=*)

    # Objective computation functions
    cdef _min_load(self, unicode resource, tcs, varname)
    cpdef min_node_load(self, unicode resource, tcs=*, varname=*)
    cpdef min_link_load(self, unicode resource, tcs=*, varname=*)
    cpdef min_latency(self, tcs=*, bool norm=*, cost_func=*, varname=*)
    cpdef max_flow(self, tcs=*, varname=*)
    cpdef compose_objectives(self, ndarray obj_arr, epoch_mode, fairness_mode, weight_arr)
    cdef _compose_obj_one_epoch(self, int epoch, ndarray obj, fairness_mode, weight_arr)
    # TODO: find a way to define a custom objective function

   # Node/link toggle functions
    cdef _req_some(self, req_type, traffic_classes=*, node_mode=*)
    cdef _req_all(self, req_type, traffic_classes=*, node_mode=*)
    cpdef req_all_nodes(self, traffic_classes=*, node_mode=*)
    cpdef req_all_links(self, traffic_classes=*)
    cpdef req_some_nodes(self, traffic_classes=*, node_mode=*)
    cpdef req_some_links(self, traffic_classes=*)
    cpdef node_budget(self, int bound, budget_func=*)

    # Solution parsing functions and general helper funcs
    cpdef solve(self)
    cpdef is_solved(self)
    cpdef get_paths(self, int epoch=*)
    cpdef get_solved_objective(self, app=*)
    cpdef get_chosen_paths(self)
    cpdef get_var_values(self)
    cpdef get_enabled_nodes(self)
    cpdef get_enabled_links(self)
    # cpdef get_vars(self)
    cpdef fix_paths(self, PPTC pptc, fix_zero_paths=*)
    cpdef save_hints(self, fname)
    cpdef load_hints(self, fname)

    cpdef write(self, fname)
    cpdef write_solution(self, fname)
    cpdef set_time_limit(self, long time)
    cpdef double get_time(self)

    # Advanced functionality functions
    cpdef relax_to_lp(self)
    cpdef get_gurobi_model(self)
    # TODO: bring back mindiff
    # TODO: MIP starts?

    cpdef get_xps(self)
    cpdef get_load_dict(self)

# cpdef add_obj_var(app, opt, double weight=*, epoch_mode=*)
# cpdef get_obj_var(app, opt)
