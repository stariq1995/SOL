# coding=utf-8
# cython: cdivision=True
from __future__ import division

from sol.topology.topologynx cimport Topology
from sol.opt.gurobiwrapper cimport OptimizationGurobi, add_obj_var, \
    add_named_constraints

from sol import logger
from sol.utils.exceptions import CompositionError
from numpy import log
#XXX: this entire module is currently tied to Gurobi


logx = [0.01,0.02,0.03,0.05,0.08,0.12,0.18,0.28,0.43,0.66,1.]
log_approx = log(logx)


cpdef compose(list apps, Topology topo, epoch_mode='max', obj_mode='weighted'):
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
    opt = OptimizationGurobi(topo)
    for app in apps:
        add_named_constraints(opt, app)
    logger.debug("Added named constraints")

    compose_resources(apps, topo, opt)
    if obj_mode == 'weighted':
        weighted_obj(apps, topo, opt, epoch_mode)
    elif obj_mode == 'propfair':
        prop_fair_obj(apps, topo, opt, epoch_mode)
    elif obj_mode == 'maxmin':
        max_min_obj(apps, topo, opt, epoch_mode)
    else:
        raise ValueError('Unknown objective composition mode')
    logger.debug("Composition complete")
    return opt

cpdef _detect_cost_conflict(apps):
    cdef int i, j
    for i in range(len(apps)):
        for j in range(i, len(apps)):
            sameresoures = set(apps[i].resourceCost.keys()).intersection(
                apps[j].resourceCost.keys())
            for r in sameresoures:
                if apps[i].resourceCost[r] != apps[j].resourceCost[r]:
                    raise CompositionError(
                        "Different costs for resources in overlapping traffic classes")
    logger.debug("No resource conflicts between apps")

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
        var = add_obj_var(app, opt, weight=1, epoch_mode=epoch_mode)
        m.addConstr(obj <= var)
    opt.get_gurobi_model().update()

cdef gini_obj(apps, Topology topo, opt):
    raise NotImplemented

cdef variance_obj(apps, Topology topo, opt):
    raise NotImplemented

cdef relative_mean_deviation_obj(apps, Topology topo, opt):
    raise NotImplemented

# TODO: introduce other fairness metrics
