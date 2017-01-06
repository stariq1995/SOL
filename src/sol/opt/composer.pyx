# coding=utf-8
# cython: profile=True
from __future__ import division
from __future__ import print_function

import six
from gurobipy import quicksum

from numpy import log
from sol.opt.gurobiwrapper cimport OptimizationGurobi, add_obj_var, \
    add_named_constraints
from sol.topology.topologynx cimport Topology

from sol.path.paths cimport PPTC
from sol.utils.exceptions import CompositionError
from sol.utils.logger import logger

#XXX: this entire module is currently tied to Gurobi


logx = [0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.28, 0.43, 0.66, 1.]
log_approx = log(logx)

cpdef compose(list apps, Topology topo, epoch_mode='max', obj_mode='weighted', globalcaps=None):
    """
    Compose multiple applications into a single optimization
    :param apps: a list of App objects
    :param topo: Topology
    :param epoch_mode: how is the objective computed across different epochs.
    Default is 'max', that is we take the maximum obj function across epochs
    :param obj_mode: type of objective composition. default is 'weighed', i.e.
     a weighted sum. 'propfair' is proportionally fair, 'maxmin' in maximizing the minimum
    :return:
    """
    logger.debug("Starting composition")

    # TODO: this merging should be a temporary workaround until better solution
    all_pptc = PPTC()
    for app in apps:
        all_pptc.update(app.pptc)

    opt = OptimizationGurobi(topo, all_pptc)
    logger.debug("Composing resources")
    compose_resources(apps, topo, opt)
    if globalcaps is not None:
        for cap in globalcaps:
            r = six.u(cap.resource) if isinstance(cap.resource, str) else cap.resource
            opt.cap(r, tcs=None, capval=cap.cap)
    if obj_mode == 'weighted':
        weighted_obj(apps, topo, opt, epoch_mode)
    elif obj_mode == 'propfair':
        prop_fair_obj(apps, topo, opt, epoch_mode)
    elif obj_mode == 'maxmin':
        max_min_obj(apps, topo, opt, epoch_mode)
    elif obj_mode == 'variance':
        variance_obj(apps, topo, opt)
    else:
        raise ValueError('Unknown objective composition mode')
    logger.debug("Adding named constraints")
    for app in apps:
        add_named_constraints(opt, app)
    logger.debug("Composition complete")
    return opt

cpdef _detect_cost_conflict(apps):
    cdef int i, j
    resourse_overlap = False
    tc_overlap = False
    # For each app pair
    for i in range(len(apps)):
        for j in range(i, len(apps)):
            # Check for overlapping resources
            sameresoures = set(list(apps[i].resourceCost.keys())) \
                .intersection(list(apps[j].resourceCost.keys()))
            for r in sameresoures:
                if apps[i].resourceCost[r] != apps[j].resourceCost[r]:
                    resourse_overlap = True
                    break
            # don't do extra work, break if at least one conflict detected
            if resourse_overlap:
                break
        if resourse_overlap:
            break
    tcs = set()
    for app in apps:
        l = list(app.pptc.tcs())
        if tcs.intersection(l):
            tc_overlap = True
            break
        tcs.update(l)

    if resourse_overlap and tc_overlap:
        raise CompositionError(
            "Different costs for resources in overlapping traffic classes")
    logger.debug("No resource conflicts between apps")
    return resourse_overlap, tc_overlap

cdef compose_resources(list apps, Topology topo, opt):
    logger.debug("Composing resources")
    _detect_cost_conflict(apps)
    node_caps = {node: topo.get_resources(node) for node in topo.nodes()}
    link_caps = {link: topo.get_resources(link) for link in topo.links()}
    for app in apps:
        for r in app.resourceCost:
            opt.consume(app.pptc, r, app.resourceCost[r],
                        {n: node_caps[n][r] for n in node_caps if
                         r in node_caps[n]},
                        {l: link_caps[l][r] for l in link_caps if
                         r in link_caps[l]})
    # cap resources
    res = set()
    for app in apps:
        res.update(app.resourceCost.keys())
    # for r in res:
    #     opt.cap(r, 1)

cdef weighted_obj(apps, Topology topo, opt, epoch_mode):
    logger.debug("Composing objectives")
    cdef double total_vol = 0
    # Compute proportions according to volume
    vols = {app: app.volume() for app in apps}
    logger.debug('App volumes: %s', vols)
    total_vol = sum(vols.values())
    for app in apps:
        add_obj_var(app, opt, vols[app] / total_vol, epoch_mode)
    opt.get_gurobi_model().update()

cdef prop_fair_obj(apps, Topology topo, opt, epoch_mode):
    logger.debug("Composing objectives with prop fairness")
    m = opt.get_gurobi_model()
    for app in apps:
        var = add_obj_var(app, opt, weight=0, epoch_mode=epoch_mode)
        m.setPWLObj(var, logx, log_approx)
    m.update()

cdef max_min_obj(apps, Topology topo, opt, epoch_mode):
    logger.debug("Composing objectives")
    m = opt.get_gurobi_model()
    obj = m.addVar(name='minobj', lb=0, obj=1)
    for app in apps:
        var = add_obj_var(app, opt, weight=0, epoch_mode=epoch_mode)
        m.addConstr(obj <= var)
    opt.get_gurobi_model().update()

cdef gini_obj(apps, Topology topo, opt):
    raise NotImplemented

cdef variance_obj(apps, Topology topo, opt):
    m = opt.get_gurobi_model()
    average = m.addVar(name='average')
    objvars = []
    for app in apps:
        var = add_obj_var(app, opt, weight=0)
        objvars.append(var)
    m.update()
    m.addConstr(average == quicksum(objvars) / len(apps))
    diffs = []
    for var in objvars:
        d = m.addVar()
        m.update()
        diffs.append(d)
        m.addConstr(d == var - average)
    m.update()
    m.setObjective(quicksum([d ** 2 for d in diffs]) / len(apps))
    m.update()

cdef relative_mean_deviation_obj(apps, Topology topo, opt):
    raise NotImplemented

# TODO: introduce other fairness metrics
