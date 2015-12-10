from collections import defaultdict

from sol.opt import getOptimization
from sol.utils.exceptions import SOLException


def _MaxMinFairness_MCF(topology, pptc, unstaturated, saturated, allocation, linkCaps):
    """ Formulate and solve a multi-commodity flow problem given the saturated
    and un-saturated commodities
    """
    opt = getOptimization()
    opt.addDecisionVariables(pptc)
    opt.addAllocateFlowConstraint({tc: pptc[tc] for tc in unstaturated})
    for i in saturated:
        opt.addAllocateFlowConstraint({tc: pptc[tc] for tc in pptc[i]}, allocation[i])

    def linkcapfunc(link, tc, path, resource):
        return tc.volBytes

    opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkCaps, linkcapfunc)
    opt.setPredefinedObjective("maxallflow")
    opt.solve()

    return opt


def iterateMaxMinFairness(topology, pptc, linkCaps):
    """ Run the iterative algorithm for max-min fairness

    ..warning:: This implementation does not use any optimizations
    like binary search

    :param topology: the topology on which we are running this
    :param pptc: paths per commodity
    :param linkCaps: link capacities for the topology
    :return paths with flow volumes assigned
    """

    # Setup saturated and unsaturated commodities
    saturated = defaultdict(lambda: [])
    unsaturated = set(pptc.keys())
    paths = defaultdict(lambda: [])

    t = []  # allocation values per each iteration
    i = 0  # iteration index
    while unsaturated:
        # Run slightly modified multi-commodity flow
        opt = _MaxMinFairness_MCF(topology, pptc, unsaturated, saturated, t, linkCaps)
        if not opt.isSolved():
            raise SOLException('No solution')
        alloc = opt.getSolvedObjective()
        t.append(alloc)
        # Check if commodity is saturated, if so move it to saturated list
        for tc in list(unsaturated):
            # NOTE: this is an inefficient non-blocking test, based on dual variables
            # More efficient methods are available
            dual = opt.getCPLEXObject().get_dual_values(opt.al(tc))
            if dual > 0:
                unsaturated.remove(tc)
                saturated[i].append(tc)
                paths[tc] = opt.getPathFractions()[tc]
        i += 1
    return paths
