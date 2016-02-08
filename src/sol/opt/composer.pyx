from gurobipy import quicksum, GRB, LinExpr, QuadExpr

from ..opt import getOptimization
from ..utils.constansts import *
from ..utils.exceptions import CompositionError

#XXX: this is currently tied to Gurobi 
def _addNamedConstraints(opt, app):
    for c in app.constraints:
        if c == ALLOCATE_FLOW:
            opt.allocateFlow(app.pptc)
        elif c == ROUTE_ALL:
            opt.routeAll(app.pptc)

def compose(apps, topo, resMode, globalNodeCaps, globalLinkCaps, 
            resourcesToShare=[]):
    opt = getOptimization('Gurobi')
    for app in apps:
        opt.addDecisionVars(app.pptc)
        _addNamedConstraints(opt, app)

    _composeResources(apps, topo, opt, nodeCaps, linkCaps, resMode)
    proportionalFairness(apps, topo, opt)
    return opt

def _composeResources(apps, topo, opt, nodeCaps, linkCaps, mode=RES_COMPOSE_MAX):
    resourceset = set()
    for a in apps:
        for r in a.getResourceNames():
            resourceset.add(r)

    # Decide how we pick resource consumptions value
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

        for app in apps:
            if app.uses(r):
                opt.consume(app.trafficClasses, r, val, nodeCaps, linkCaps)

def _proportionalFairness(apps, topo, opt, to='volume'):
    cdef double totalVol = 0
    if to.lower() == 'volume':
        vols = {app: sum([tc.volFlows for tc in app.trafficClasses]) for app in apps}
        totalVol = sum(vols.values())
        for app in apps:
            v = _addObjVar(app, topo, opt)
            v.Obj = vols[app] / totalVol
        opt.getGurobiModel().update()
    else:
        raise CompositionError('Unknown proportion when using proportional fairness')

def _proportionalFairnessResource(apps, topo, opt, resource, to='volume'):
    cdef double totalVol = 0
    if to.lower() == 'volume':
        vols = {app: sum([tc.volFlows for tc in app.trafficClasses]) for app in apps}
        totalVol = sum(vols.values())
        # depending on what resource means write the fairness equations
        # if the resource is portion of a global resource
        
        #TODO: need resource in path primitive!
        for app in apps:
            for tc in app.pptc:
                for pi, p in enumerate(app.pptc[tc]):
                    if resource in p:
                        pass


def _addObjVar(app, topo, opt):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.minLinkLoad('bw', 0)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.minLatency(topo, app.trafficClasses, 0)
    else:
        raise CompositionError("Unknown objective")

def getObjVar(app, opt):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.getMaxLinkLoad('bw', False)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.getLatency(False)
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
#         _addObjVar(app, topo, opt)
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
