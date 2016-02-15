from gurobipy import LinExpr

from sol import App
from sol.opt.varnames import ALLOCATE_FLOW, ROUTE_ALL, xp, CAP_LINKS, CAP_NODES, SHARE_PROPORTIONAL_VOLUME, SHARE_EQUAL, \
    SHARE_NUM_APPS
from ..opt import getOptimization
from ..utils.constansts import *
from ..utils.exceptions import CompositionError

#XXX: this is currently tied to Gurobi 
def addNamedConstraints(opt, app):
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

def compose(apps, topo, overlapResMode, resourcesToShare, resShareMode=SHARE_PROPORTIONAL_VOLUME,
            objShareMode=SHARE_PROPORTIONAL_VOLUME):
    opt = getOptimization('Gurobi')
    for app in apps:
        opt.addDecisionVars(app.pptc)
        addNamedConstraints(opt, app)

    _composeResources(apps, topo, opt, overlapResMode)
    if objShareMode == SHARE_PROPORTIONAL_VOLUME:
        _proportionalFairness(apps, topo, opt)
    elif objShareMode == SHARE_NUM_APPS:
        for app in apps:
            v = addObjVar(app, topo, opt, 1.0/len(apps))
    elif objShareMode == SHARE_EQUAL:
        for app in apps:
            addObjVar(app, topo, opt, 1)
    else:
        raise ValueError
    for r in resourcesToShare:
        _proportionalFairnessResource(apps, topo, opt, r)
    return opt

def _composeResources(apps, topo, opt, mode):
    resourceset = set()
    for a in apps:
        for r in a.getResourceNames():
            resourceset.add(r)

    # Decide how we pick resource consumption values
    for r in resourceset:
        cost = []
        for app in apps:
            if app.uses(r):
                cost.append(app.resources[r])
        val = None
        if mode == RES_COMPOSE_MAX:
            val = max(cost)
        elif mode == RES_COMPOSE_SUM:
            val = sum(cost)
        elif mode == RES_COMPOSE_CONFLICT:
            if len(set(cost)) != 1:
                raise CompositionError("Resource composition conflict")
            val = cost[0]

        nodeCaps = {node: topo.getResources(node)[r].capacity for node in topo.nodes() if r in topo.getResources(node)}
        linkCaps = {link: topo.getResources(link)[r].capacity for link in topo.links() if r in topo.getResources(link)}
        for app in apps:
            if app.uses(r):
                opt.consume(app.pptc, r, val, nodeCaps, linkCaps)

def _proportionalFairness(apps, topo, opt, to='volume'):
    cdef double totalVol = 0
    if to.lower() == 'volume':
        vols = {app: sum([tc.volFlows for tc in app.pptc]) for app in apps}
        totalVol = sum(vols.values())
        for app in apps:
            v = addObjVar(app, topo, opt)
            v.Obj = vols[app] / totalVol
        opt.getGurobiModel().update()
    else:
        raise CompositionError('Unknown proportion when using proportional fairness')

def _proportionalFairnessResource(apps, topo, opt, resource, to='volume'):
    cdef double totalVol = 0
    m = opt.getGurobiModel()
    if to.lower() == 'volume':
        vols = {app: sum([tc.volFlows for tc in app.pptc]) for app in apps}
        appToExpr = {}
        for app in apps:
            # m.addVar(name='{}_{}'.format(app.name, resource.name))
            # m.update()
            e = LinExpr()
            pptcFiltered = {tc: [p for p in app.pptc[tc] if resource in p] for tc in app.pptc}
            for tc in pptcFiltered:
                for path in pptcFiltered[tc]:
                    e.add(opt.v(xp(tc, path)))
            appToExpr[app] = e
        for app1, app2 in zip(appToExpr.keys(), appToExpr.keys()[1:]):
            m.addConstr(appToExpr[app1] == (vols[app1] / vols[app2]) * appToExpr[app2],
                        name='FairShare.{}'.format(resource.name))
            m.update()

def addObjVar(app, topo, opt, weight=0):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.minLinkLoad('bw', weight)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.minLatency(topo, app.objpptc, weight)
    else:
        raise CompositionError("Unknown objective")

def getObjVar(app, opt, value=False):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.getMaxLinkLoad('bw', value)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.getLatency(value)
    else:
        raise CompositionError("Unknown objective")

def pinTraffic(app1, app2, double ratio):
    raise NotImplemented

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
