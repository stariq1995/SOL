# coding=utf-8
from __future__ import division

from sol.opt.formulation import kickStartOptimization
from sol.opt.topology import provisioning
from sol.opt.topology.generators import generateCompleteTopology
from sol.opt.topology.provisioning import generateTrafficClasses

from sol.path import nullPredicate

if __name__ == '__main__':

    # ==============
    # Fake some data
    # ==============
    topo = generateCompleteTopology(8)
    # ingress-egress pairs
    iePairs = provisioning.generateIEpairs(topo)
    # generate traffic matrix
    trafficMatrix = provisioning.computeUniformTrafficMatrixPerIE(
        iePairs, 10 ** 6)
    # compute traffic classes, only one class
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    linkcaps = provisioning.provisionLinks(topo, trafficClasses, 1)
    # do not load links more than 50%
    linkConstrCaps = {(u, v): .5 for u, v, data in topo.links()}

    # ==============
    # Optimize
    # ==============
    linkcapfunc = lambda link, tc, path, resource: tc.volBytes/linkcaps[link]
    # Start our optimization! SOL automatically takes care of the paths behind the scenes
    opt, pptc = kickStartOptimization(topo, trafficClasses, nullPredicate, 'shortest', 5)
    # Traffic must flow!
    opt.allocateFlow(pptc)
    # Traffic must not overload links!
    opt.capLinks(pptc, 'bandwidth', linkConstrCaps, linkcapfunc)
    # Push as much traffic as we can!
    opt.setPredefObjective('maxminflow')

    opt.solve()
    print opt.getSolvedObjective()  # let's see how much traffic we managed to push
    print opt.getPathFractions(pptc)  # this tells you how much traffic goes on each path

    ####
    # The answer is: 0.5 (50%). Because our links were constrained
    ####
