# coding=utf-8
from __future__ import division
from sol.optimization.formulation import kickStartOptimization
from sol.optimization.path.predicates import nullPredicate
from sol.optimization.topology import provisioning
from sol.optimization.topology.generators import generateCompleteTopology
from sol.optimization.topology.provisioning import generateTrafficClasses

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
    opt.addAllocateFlowConstraint(pptc)
    # Traffic must not overload links!
    opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkConstrCaps, linkcapfunc)
    # Push as much traffic as we can!
    opt.setPredefinedObjective('maxminflow')

    opt.solve()
    print opt.getSolvedObjective()  # let's see how much traffic we managed to push

    ####
    # The answer is: 0.5 (50%). Because our links were constrained
    ####
