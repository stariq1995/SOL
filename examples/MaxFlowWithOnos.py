# coding=utf-8
from __future__ import division
from sol.optimization.formulation import kickStartOptimization
from sol.optimization.path.predicates import nullPredicate
from sol.optimization.topology import provisioning
from sol.optimization.topology.generators import generateCompleteTopology
from sol.optimization.topology.provisioning import generateTrafficClasses
from sol.sdn.controllerUtil import computeSplit
from sol.sdn.onosWrapper import ONOSInterface

if __name__ == '__main__':

    # ==============
    # Fake some data
    # ==============
    onos = ONOSInterface("192.168.99.100:8181")
    topo = onos.getTopology()
    # topo = generateCompleteTopology(8)
    # ingress-egress pairs
    iePairs = provisioning.generateIEpairs(topo)
    # generate traffic matrix
    trafficMatrix = provisioning.computeUniformTrafficMatrixPerIE(
        iePairs, 10 ** 6)
    # compute traffic classes, only one class
    trafficClasses = generateTrafficClasses(iePairs, trafficMatrix, {'allTraffic': 1},
                                            {'allTraffic': 2000})
    for tc in trafficClasses:
        tc.srcIPPrefix = "10.0.0.{}/32".format(int(tc.src.lstrip(":of")))
        tc.dstIPPrefix = "10.0.0.{}/32".format(int(tc.dst.lstrip(":of")))
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
    # print opt.getPathFractions(pptc)  # this tells you how much traffic goes on each path

    routes = {}
    for tc, paths in opt.getPathFractions(pptc).iteritems():
        routes.update(computeSplit(tc, paths, 0, False))
    print(routes)
    onos.pushRoutes(routes)
