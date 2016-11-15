# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool
from numpy cimport ndarray

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:

    cdef public opt
    cdef public Topology topo
    cdef public dict expr
    cdef public dict _varindex
    cdef bool _do_time
    cdef double _time
    cdef public _load_dict
    cdef dict _res_dict
    cdef int num_epochs
    cdef ndarray _load_array
    cdef ndarray _xps

    cpdef _add_decision_vars(self, dict pptc)
    cdef _add_binary_vars(self, dict pptc, vtypes)
    cpdef allocate_flow(self, pptc, allocation=*)
    cpdef cap_num_paths(self, pptc, int max_paths)
    cpdef enforce_single_path(self, pptc, traffic_classes)
    cdef _disable_paths(self, pptc, traffic_classes=*)
    cdef _min_load(self, unicode resource, tcs, unicode prefix, weight, epoch_mode, name)
    cpdef min_node_load(self, unicode resource, tcs, weight=*, epoch_mode=*, name=*)
    cpdef min_link_load(self, unicode resource, tcs, weight=*, epoch_mode=*, name=*)
    cpdef solve(self)
    cpdef get_path_fractions(self, pptc, bool flow_carrying_only=*)
    cpdef route_all(self, pptc)
    cpdef get_solved_objective(self)
    cpdef is_solved(self)
    cpdef v(self, unicode varname)
    cdef bool _has_var(self, unicode varname)
    cpdef get_chosen_paths(self, pptc)
    cpdef set_time_limit(self, long time)
    cpdef write(self, unicode fname)
    cpdef write_solution(self, unicode fname)
    cpdef get_var_values(self)
    cpdef get_vars(self)
    cpdef node_budget(self, budgetFunc, int bound)
    cpdef min_latency(self, pptc, weight=*, bool norm=*, epoch_mode=*, name=*)
    cpdef max_flow(self, pptc, weight=*, name=*)
    cpdef max_min_flow(self, pptc, weight=*, name=*)
    cdef _req_some(self, pptc, traffic_classes=*, req_type=*)
    cdef _req_all(self, pptc, traffic_classes=*, req_type=*)
    cpdef req_all_nodes(self, pptc, traffic_classes=*)
    cpdef req_all_links(self, pptc, traffic_classes=*)
    cpdef req_some_nodes(self, pptc, traffic_classes=*)
    cpdef req_some_links(self, pptc, traffic_classes=*)
    cpdef double get_time(self)
    cpdef relax_to_lp(self)
    cpdef get_latency(self, bool value=*)
    cdef _get_load(self, unicode resource, unicode prefix, bool value=*)
    cpdef get_max_link_load(self, unicode resource, bool value=*)
    cpdef get_max_node_load(self, unicode resource, bool value=*)
    cpdef get_maxflow(self, bool value=*)
    cpdef consume(self, pptc, unicode resource, double cost, node_caps,
                  link_caps)
    cpdef consume_per_path(self, pptc, unicode resource_name, double cost,
                           node_caps, link_caps)
    cpdef cap(self, unicode resource, double capval=*)
    cpdef fix_paths(self, pptc)
    cpdef get_xps(self)
    cpdef get_fractions(self)

cpdef add_obj_var(app, opt, weight=*, epoch_mode=*)
cpdef get_obj_var(app, opt)
cdef add_named_constraints(opt, app)
