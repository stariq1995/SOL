from ..utils.exceptions import CompositionError
from ..opt import getOptimization
from ..utils.constansts import *
import numpy
from gurobipy import QuadExpr, LinExpr

def composeSingleLP(apps, topo, resMode, objMode):
    opt = getOptimization('Gurobi')
    for app in apps:
        opt.addDecisionVars(app.trafficClasses)
        opt.allocateFlow(app.trafficClasses)
        opt.routeAll(app.trafficClasses)

    composeResources(apps, topo, opt, resMode)
    composeObjectives(apps, topo, opt, objMode)
    return opt


def composeResources(apps, topo, opt, mode=RES_COMPOSE_MAX):
    resourceset = set()
    for a in apps:
        for r in a.getResourceNames():
            resourceset.add(r)
    for r in resourceset:
        resapps = []
        for app in apps:
            if app.uses(r):
                resapps.append(a.resources[r])

        # print(resapps, set(resapps))
        val = None
        if mode == RES_COMPOSE_MAX:
            val = max(resapps)
        elif mode == RES_COMPOSE_SUM:
            val = sum(resapps)
        elif mode == RES_COMPOSE_CONFLICT:
            if len(set(resapps)) != 1:
                raise CompositionError("Resource composition conflict")
            val = resapps[0]

        for app in apps:
            if app.uses(r):
                opt.consume(app.trafficClasses, r, val, {node: [] for node in topo.nodes(False)},
                            {link: {'bw': 1} for link in topo.links(False)})


def proportionalFairness(apps, to='volume'):
    cdef double totalVol = 0
    vols = []
    for app in apps:
        vol = sum([tc.volFlows for tc in app.trafficClasses])
        vols.append(vol)
        totalVol += vol
    return [vol/totalVol for vol in vols]

def addObjVar(app, opt, topo=None):
    if app.obj.lower() == MIN_LINK_LOAD:
        return opt.minLinkLoad('bw', 0)
    elif app.obj.lower() == MIN_LATENCY:
        return opt.minLatency(topo, app.trafficClasses, 0)
    else:
        raise CompositionError("Unknown objective")


cpdef axiomFairness(apps, opt, float beta):
    ratio = QuadExpr()
    denom = LinExpr()
    vars = []
    for app in apps:
        v = addObjVar(app)
        vars.append(v)
        denom += v
    for app in apps:
        ratio += (v/denom)^(1-beta)
    opt.getModel().setObj(numpy.sign(1-beta)*(ratio^(1/beta)))






