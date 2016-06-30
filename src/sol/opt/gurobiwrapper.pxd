# coding=utf-8

from sol.topology.topologynx cimport Topology
from cpython cimport bool

# noinspection PyClassicStyleClass
cdef class OptimizationGurobi:

    cdef public opt
    cdef public Topology topo
    cdef public dict expr
    cdef public dict _varindex
    cdef bool _do_time
    cdef double _time

    cpdef _add_decision_vars(self, dict pptc)
    cdef _add_binary_vars(self, dict pptc, vtypes)
    cpdef allocate_flow(self, pptc, allocation=*)
    cpdef cap_num_paths(self, pptc, int max_paths)
    cpdef enforce_single_path(self, pptc, traffic_classes)
    cdef _disable_paths(self, pptc, traffic_classes=*)
    cdef _min_load(self, str resource, tc, str prefix, float weight, epoch_mode)
    cpdef min_node_load(self, str resource, tc, float weight=*, epoch_mode=*)
    cpdef min_link_load(self, str resource, tc, float weight=*, epoch_mode=*)
    cpdef solve(self)
    cpdef get_path_fractions(self, pptc, bool flow_carrying_only=*)
    cpdef route_all(self, pptc)
    cpdef get_solved_objective(self)
    cpdef is_solved(self)
    cdef v(self, str varname)
    cdef bool _has_var(self, str varname)
    cpdef get_chosen_paths(self, pptc)
    cdef _dump_expressions(self)
    cpdef set_time_limit(self, long time)
    cpdef write(self, str fname)
    cpdef write_solution(self, str fname)
    cpdef get_var_values(self)
    cpdef node_budget(self, budgetFunc, int bound)
    cpdef min_latency(self, pptc, double weight=*, bool norm=*, epoch_mode=*)
    cpdef max_flow(self, pptc, double weight=*)
    cdef _req_some(self, pptc, traffic_classes=*, req_type=*)
    cdef _req_all(self, pptc, traffic_classes=*, req_type=*)
    cpdef req_all_nodes(self, pptc, traffic_classes=*)
    cpdef req_all_links(self, pptc, traffic_classes=*)
    cpdef req_some_nodes(self, pptc, traffic_classes=*)
    cpdef req_some_links(self, pptc, traffic_classes=*)
    # cpdef enable_timing(self)
    cpdef double get_time(self)
    cpdef relax_to_lp(self)
    cpdef get_latency(self, value=*)
    cdef _get_load(self, str resource, str prefix, bool value=*)
    cpdef get_max_link_load(self, str resource, bool value=*)
    cpdef get_max_node_load(self, str resource, bool value=*)
    cpdef consume(self, pptc, str resource_name, double cost, node_caps,
                  link_caps)
    cdef _consume_helper(self, tc, path, node_or_link, int num_epochs,
                         str prefix, str resource_name, double cost, caps)

cpdef add_obj_var(app, opt, double weight=*, epoch_mode=*)
cpdef get_obj_var(app, opt)
cdef add_named_constraints(opt, app)
