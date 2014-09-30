""" Contains common configuration values for eval scripts and such
"""

import os
import inspect

from panacea.lps.topology.topology import RocketFuelTopology, FatTreeTopology


__currdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))

ALLtopologyNames = sorted([
    'asAtt', 'asCogent', 'asGarr',
    'asInternet2',
    'asIon',
    # 'asKentucky'
])

topologyNames = sorted([
    # 'asAtt', 'asCogent',
    'asGarr',
    'asInternet2',
    # 'asIon',
    # 'asKentucky'
])

dcTopologyNames = ['k4', 'k6', 'k8', 'k10', 'k12']

datadir = os.path.normpath(__currdir + '/../../data/AS/')
pathdir = os.path.normpath(__currdir + '/../../data/paths/')
csvdir = os.path.normpath(__currdir + '/../../data/csv/')
outdir = os.path.normpath(__currdir + '/../../../../run/stfu-formulations/')
graphdir = os.path.normpath(__currdir + '/../../../../graphs/stfu/')
soldir = os.path.normpath(__currdir + '/../../../../run/stfu-formulationsol/')
tabledir = os.path.normpath(__currdir + '/../../../../paper/nsdi15/textables/')


def loadTopologies(names):
    """ Loads all the topologies from pre-defined places on disk
    :param names: names of topologies to load
    :return: list of :py:class:`~panacea.optimization.topology.Topology` objects
    """
    topos = []
    for name in names:
        if name.startswith('k'):
            topos.append(FatTreeTopology(name))
        else:
            topos.append(RocketFuelTopology(name))
    for t in topos:
        try:
            t.loadGraph(datadir + os.path.sep + t.name + '.graphml')
        except IOError as e:
            print e
            continue
    return topos


frameworkName = 'SOL'

LPconfig = {
    'overprovision': 3,
    'constraints': ['link']
}

solcodesGood = [1, 101, 102, 107, 11]
