# coding=utf-8

from collections import defaultdict
import copy
import json
import re
import itertools

import networkx
import netaddr

import requests
from requests.auth import HTTPBasicAuth
from sol.optimization.topology.topology import Topology
from sol.utils.exceptions import ControllerException


class ONOSInterface(object):
    """
        Manages OpenDaylight controller using its REST interface.
        This is a prototype implementation
    """

    def _computeSplit(self, k, paths, blockbits, mindiff):
        srcnet = netaddr.IPNetwork(k.srcprefix)
        dstnet = netaddr.IPNetwork(k.dstprefix)
        # Diffenrent length of the IP address based on the version
        ipbits = 32
        if srcnet.version == 6:
            ipbits = 128
        # Set up our blocks. Block is a pair of src-dst prefixes
        assert blockbits <= ipbits - srcnet.prefixlen
        assert blockbits <= ipbits - dstnet.prefixlen
        numblocks = len(srcnet) * len(dstnet) / (2 ** (2 * blockbits))
        newmask1 = srcnet.prefixlen + blockbits
        newmask2 = srcnet.prefixlen + blockbits
        blockweight = 1.0 / numblocks # This is not volume-aware
        assigned = defaultdict(lambda: [])
        if not mindiff:
            # This is the basic version, no min-diff required.
            assweight = 0
            index = 0
            path = paths[index]
            # Iterate over the blocks and pack then into paths
            for block in itertools.product(srcnet.subnet(newmask1),
                                           dstnet.subnet(newmask2)):
                if index >= len(paths):
                    raise Exception('no bueno')

                assigned[path].append(block)
                assweight += blockweight
                if assweight >= path.getNumFlows():
                    # print path.getNumFlows(), assweight
                    assweight = 0
                    index += 1
                    if index < len(paths):
                        path = paths[index]
        else:
            leftovers = []
            # iteration one, remove any exess blocks and put them into leftover
            # array
            for p in paths:
                oldsrc, olddst = self._pathmap[p]
                oldweight = len(oldsrc) * len(olddst) / (2 ** blockbits)
                if p.getNumFlows() < oldweight:
                    assweight = 0
                    for block in itertools.product(oldsrc.subnet(newmask1),
                                                   olddst.subnet(newmask2)):
                        assigned[p].append(block)
                        assweight += blockweight
                        if assweight >= p.getNumFlows():
                            leftovers.append(block)
            # iteration two, use the leftovers to pad paths where fractions
            # are too low
            for p in paths:
                oldsrc, olddst = self._pathmap[p]
                oldweight = len(oldsrc) * len(olddst) / (2 ** blockbits)
                if p.getNumFlows() > oldweight:
                    assweight = oldweight
                    while leftovers:
                        block = leftovers.pop(0)
                        assigned[p].append(block)
                        assweight += blockweight
                        if assweight >= p.getNumFlows():
                            break
            assert len(leftovers) == 0
        return assigned
        # TODO: implement more sophisticated volume-aware splitting
        # TODO: corner case: splitting if just one IP per src/dst?

    def generateRoutes(self, pptc, daylightGraph, blockbits=5, convertoffset=0):
        """
        Take the output of the optimization and generate OpenDaylight routes.

        :param pptc: path per traffic class obtained from the optimization.
            .. warning::
                Assumes that that all non-flow-carrying paths have been filtered
                out.

        :param daylightGraph: the OpenDaylight topology
        :param blockbits: How many bits define a block of IP adresses.
            The smaller the number, the more fine-grained splitting is.
            Default is 5 bits.

        :param convertoffset: offset to use when converting paths.
            If you have topology that uses with nodeID of 0, set this to 1.
        :return: a list of routes to be installed on the switches.
        """
        routeList = []
        for k in pptc:
            numpaths = len(pptc[k])
            if numpaths > 1:
                # The complex case, need to compute a split between paths
                assigned = self._computeSplit(k, pptc[k], blockbits, False)
                for path in assigned:
                    sources, dests = zip(*assigned[path])
                    subsrcprefix = netaddr.cidr_merge(sources)
                    subdstprefix = netaddr.cidr_merge(dests)
                    # print path, subsrcprefix, subdstprefix

                    #TODO: test the correctness of this better
                    assert len(subsrcprefix) == len(subdstprefix)
                    for s, d in itertools.izip(subsrcprefix, subdstprefix):
                        routeList.append((convertPath(path, offset=convertoffset),
                                          daylightGraph, str(s), str(d)))
            else:
                # Easy case, only one flow-carrying path
                routeList.append((convertPath(pptc[k][0], offset=convertoffset),
                                  daylightGraph,
                                  k.srcprefix, k.dstprefix))
        return routeList

    def pushRoutes(self, routeList):
        """
        Push a list of routes using REST API. (See :py:func:`generateRoutes` for route generation)

        :param routeList: list of routes/paths
        """

    def getTopology(self, controllerHost="localhost:8181"):
        resp = requests.get("http://{}/onos/v1/devices".format(controllerHost))
        resp.raise_for_status()
        devices = resp.json()
        resp = requests.get("http://{}/onos/v1/links".format(controllerHost))
        resp.raise_for_status()
        links = resp.json()
        print links

        G = networkx.Graph()
        G.add_nodes_from(devices)
        G.add_edges_from(links)

        return Topology('onosTopology', G)


if __name__ == "__main__":
    o = ONOSInterface()
    print o.getTopology("192.168.99.100:8181")
    # simple test
    resp = requests.post("http://localhost:8181/sol/install", data=json.dumps([{
        "nodes":[1, 2, 3],
        "srcprefix":"10.0.0.0/8",
        "dstprefix":"10.0.0.0/8",
        "srcport": "90",
        "dstport": "90"
    }]), headers={"content-type":"application/json"})
    resp.raise_for_status()
