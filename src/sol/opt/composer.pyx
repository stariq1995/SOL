# coding=utf-8
import itertools
import operator
from gurobipy import LinExpr, quicksum

from sol.opt.varnames import ALLOCATE_FLOW, ROUTE_ALL, CAP_LINKS, CAP_NODES, MIN_LINK_LOAD, MIN_LATENCY
from sol.opt.varnames cimport xp
from sol.topology.topology cimport Topology
from sol.opt import getOptimization
from sol.utils.exceptions import CompositionError

#FIXME: this entire module is currently tied to Gurobi

cdef addNamedConstraints(opt, app):
    opt.addDecisionVars(app.pptc)
    for c in app.constraints:
        if c == ALLOCATE_FLOW:
            opt.allocateFlow(app.pptc)
        elif c == ROUTE_ALL:
            opt.routeAll(app.pptc)
        elif c[0] == CAP_LINKS:
            opt.capLinks(app.pptc, *c[1:])
        elif c[0] == CAP_NODES:
            opt.capNodes(app.pptc, *c[1:])
        else:
            raise CompositionError("Unsupported constraint type")

cpdef compose(list apps, Topology topo):
    opt = getOptimization('Gurobi')
    for app in apps:
        opt.addDecisionVars(app.pptc)
        addNamedConstraints(opt, app)

    _proportionalFairness(apps, topo, opt)
    _composeResources(apps, topo, opt)
    return opt

cpdef detectCostConflict(list apps):
    cdef int i, j
    for i in range(len(apps)):
        for j in range(i, len(apps)):
            sameresoures = set(apps[i].resourceCost.keys()).intersection(apps[j].resourceCost.keys())
            for r in sameresoures:
                if apps[i].resourceCost[r] != apps[j].resourceCost[r]:
                    raise CompositionError("Different costs for resources in overlapping traffic classes")

cdef _composeResources(list apps, Topology topo, opt):
    detectCostConflict(apps)
    for app in apps:
        for r in app.resourceCost:
            # TODO: optimize so capacities are not re-computed every time. Compute once for each type of resource
            nodeCaps = {node: topo.getResources(node)[r] for node in topo.nodes() if r in topo.getResources(node)}
            linkCaps = {link: topo.getResources(link)[r] for link in topo.links() if r in topo.getResources(link)}
            print linkCaps
            opt.consume(app.pptc, r, app.resourceCost[r], nodeCaps, linkCaps)

cdef _proportionalFairness(apps, Topology topo, opt):
    cdef double totalVol = 0
    # Compute proportions according to volume
    vols = {app: sum([tc.volFlows for tc in app.pptc]) for app in apps}
    totalVol = sum(vols.values())
    for app in apps:
        v = addObjVar(app, topo, opt)
        v.Obj = vols[app] / totalVol
    opt.getGurobiModel().update()

def addObjVar(app, Topology topo, opt, double weight=0):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.minLinkLoad('bw', weight)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.minLatency(topo, {tc: app.pptc[tc] for tc in app.objTC}, weight)
    else:
        raise CompositionError("Unknown objective")

def getObjVar(app, Topology opt, value=False):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.getMaxLinkLoad('bw', value)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.getLatency(value)
    else:
        raise CompositionError("Unknown objective")

# cpdef maxMinRatio(apps, topo, opt):
#     m = opt.getGurobiModel()
#     ratio = m.addVar(name='maxRatio', lb=0)
#     m.update()
#     m.setObjective(LinExpr(ratio), sense=GRB.MINIMIZE)
#     m.update()
#     print apps
#     for app in apps:
#         addObjVar(app, topo, opt)
#     m.update()
#     for app in apps:
#         appratio = m.addVar(name=app.name + 'ratio', lb=0)
#         m.update()
#         m.addConstr(ratio >= appratio) # >= means max ratio
#         m.update()
#         e = quicksum([getObjVar(app2, opt) for app2 in apps])
#         m.addQConstr(e - appratio * getObjVar(app, opt) == 0)
#     m.update()

# cpdef minimizeMaxRatio(apps, topo, opt):
#     m = opt.getGurobiModel()
#     # print apps
#     for app in apps:
#         addObjVar(app, topo, opt)
#     o = LinExpr()
#     o.add(len(apps) * quicksum([getObjVar(app2, opt) for app2 in apps]))
#     for app in apps:
#         appratio = m.addVar(name=app.name + 'ratio', lb=0)
#         m.update()
#         o.add(appratio)
#         e = quicksum([getObjVar(app2, opt) for app2 in apps])
#         m.addQConstr(appratio * getObjVar(app, opt) >= e)
#     m.setObjective(o)
#     m.update()
