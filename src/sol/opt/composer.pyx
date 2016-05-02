# coding=utf-8

from sol.opt.varnames import ALLOCATE_FLOW, ROUTE_ALL, CAP_LINKS, CAP_NODES, \
    MIN_LINK_LOAD, MIN_LATENCY
from sol.topology.topology cimport Topology
from sol.opt.gurobiwrapper cimport OptimizationGurobi
from sol.utils.exceptions import CompositionError

#FIXME: this entire module is currently tied to Gurobi

cdef add_named_constraints(opt, app):
    opt.addDecisionVars(app.pptc)
    for c in app.constraints:
        if c == ALLOCATE_FLOW:
            opt.allocateFlow(app.pptc)
        elif c == ROUTE_ALL:
            opt.route_all(app.pptc)
        elif c[0] == CAP_LINKS:
            opt.capLinks(app.pptc, *c[1:])
        elif c[0] == CAP_NODES:
            opt.capNodes(app.pptc, *c[1:])
        else:
            raise CompositionError("Unsupported constraint type")

cpdef compose(list apps, Topology topo):
    """
    Compose multiple applications into a single optimization
    :param apps: a list of App objects
    :param topo: Topology
    :return:
    """
    opt = OptimizationGurobi()
    for app in apps:
        opt.addDecisionVars(app.pptc)
        add_named_constraints(opt, app)

    _prop_fair_obj(apps, topo, opt)
    _compose_resources(apps, topo, opt)
    return opt

cpdef _detect_cost_conflict(list apps):
    cdef int i, j
    for i in range(len(apps)):
        for j in range(i, len(apps)):
            sameresoures = set(apps[i].resourceCost.keys()).intersection(
                apps[j].resourceCost.keys())
            for r in sameresoures:
                if apps[i].resourceCost[r] != apps[j].resourceCost[r]:
                    raise CompositionError(
                        "Different costs for resources in overlapping traffic classes")

cdef _compose_resources(list apps, Topology topo, opt):
    _detect_cost_conflict(apps)
    nodeCaps = {node: topo.getResources(node) for node in topo.nodes()}
    linkCaps = {link: topo.getResources(link) for link in topo.links()}
    for app in apps:
        for r in app.resourceCost:
            opt.consume(app.pptc, r, app.resourceCost[r],
                        {n: nodeCaps[n][r] for n in nodeCaps if
                         r in nodeCaps[n]},
                        {l: linkCaps[l][r] for l in linkCaps if
                         r in linkCaps[l]})

cdef _prop_fair_obj(apps, Topology topo, opt):
    cdef double totalVol = 0
    # Compute proportions according to volume
    vols = {app: sum([tc.volFlows for tc in app.pptc]) for app in apps}
    totalVol = sum(vols.values())
    for app in apps:
        v = add_obj_var(app, topo, opt)
        v.Obj = vols[app] / totalVol
    opt.get_gurobi_model().update()

cpdef add_obj_var(app, Topology topo, opt, double weight=0):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.minLinkLoad('bw', weight)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.minLatency(topo, {tc: app.pptc[tc] for tc in app.objTC},
                              weight)
    else:
        raise CompositionError("Unknown objective")

# cpdef getObjVar(app, Topology opt, value=False):
#     if app.obj.lower() == MIN_LINK_LOAD:
#         return opt.getMaxLinkLoad('bw', value)
#     elif app.obj.lower() == MIN_LATENCY:
#         return opt.getLatency(value)
#     else:
#         raise CompositionError("Unknown objective")
