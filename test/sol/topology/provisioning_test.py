# coding=utf-8
import sol.topology.provisioning as prov

from sol.topology.generators import generateCompleteTopology


def testPairGeneration():
    topo = generateCompleteTopology(3)
    pairs = prov.generateIEpairs(topo)
    assert pairs == [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]
