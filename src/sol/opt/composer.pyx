# coding=utf-8
# cython: cdivision=True
from __future__ import division

from sol.topology.topologynx cimport Topology
from sol.opt.gurobiwrapper cimport OptimizationGurobi, add_obj_var, \
    add_named_constraints

from sol import logger
from sol.utils.exceptions import CompositionError

#XXX: this entire module is currently tied to Gurobi

cpdef compose(list apps, Topology topo, epoch_mode='max'):
    """
    Compose multiple applications into a single optimization
    :param apps: a list of App objects
    :param topo: Topology
    :return:
    """
    logger.debug("Starting composition")
    opt = OptimizationGurobi(topo)
    for app in apps:
        add_named_constraints(opt, app)
    logger.debug("Added named constraints")

    all_tc = set()
    for app in apps:
        all_tc.update(app.pptc)
    cdef int num_tcs = len(all_tc)
    compose_resources(apps, topo, opt)
    prop_fair_obj(apps, topo, opt, epoch_mode)
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

cdef prop_fair_obj(apps, Topology topo, opt, epoch_mode):
    logger.debug("Composing objectives")
    cdef double total_vol = 0
    # Compute proportions according to volume
    vols = {app: app.volume() for app in apps}
    logger.debug('App volumes: %s', vols)
    total_vol = sum(vols.values())
    for app in apps:
        add_obj_var(app, opt, vols[app] / total_vol, epoch_mode)
    opt.get_gurobi_model().update()

# TODO: introduce other fairness metrics
