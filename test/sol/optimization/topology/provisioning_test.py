# coding=utf-8
from sol.optimization.topology.generators import generateCompleteTopology
import sol.optimization.topology.provisioning as prov

def testPairGeneration():
    topo = generateCompleteTopology(3)
    pairs = prov.generateIEpairs(topo)
    assert pairs == [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]