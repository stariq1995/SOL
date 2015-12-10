from ..utils.exceptions import CompositionError
from ..opt import getOptimization
from ..utils.constansts import *


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


def composeObjectives(apps, topo, opt, mode):
    # Right now we only support a couple. expand
    for app in apps:
        if app.Obj.lower() == MIN_LINK_LOAD:
            opt.minLinkLoad('bw', 1 / len(apps))
        elif app.Obj.lower() == MIN_LATENCY:
            opt.minLatency(topo, app.trafficClasses, 1 / len(apps))
        else:
            raise CompositionError("Unknown objective")
