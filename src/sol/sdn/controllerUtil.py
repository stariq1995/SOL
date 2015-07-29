# coding utf-8
from collections import defaultdict
import itertools

import netaddr


def computeSplit(k, paths, blockbits):
    srcnet = netaddr.IPNetwork(k.srcIPPrefix)
    dstnet = netaddr.IPNetwork(k.dstIPPrefix)
    assigned = defaultdict(lambda: [])

    # optimize for the common case of one path:
    if len(paths) == 1:
        assigned[paths[0]].append((srcnet, dstnet))
        return assigned

    # otherwise we have to do the block-splitting business

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
    blockweight = 1.0 / numblocks  # This is not volume-aware
    # if not mindiff:
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
    # else:
    #     leftovers = []
    #     # iteration one, remove any exess blocks and put them into leftover
    #     # array
    #     for p in paths:
    #         oldsrc, olddst = self._pathmap[p]
    #         oldweight = len(oldsrc) * len(olddst) / (2 ** blockbits)
    #         if p.getNumFlows() < oldweight:
    #             assweight = 0
    #             for block in itertools.product(oldsrc.subnet(newmask1),
    #                                            olddst.subnet(newmask2)):
    #                 assigned[p].append(block)
    #                 assweight += blockweight
    #                 if assweight >= p.getNumFlows():
    #                     leftovers.append(block)
    #     # iteration two, use the leftovers to pad paths where fractions
    #     # are too low
    #     for p in paths:
    #         oldsrc, olddst = self._pathmap[p]
    #         oldweight = len(oldsrc) * len(olddst) / (2 ** blockbits)
    #         if p.getNumFlows() > oldweight:
    #             assweight = oldweight
    #             while leftovers:
    #                 block = leftovers.pop(0)
    #                 assigned[p].append(block)
    #                 assweight += blockweight
    #                 if assweight >= p.getNumFlows():
    #                     break
    #     assert len(leftovers) == 0
    for path in assigned:
        sources, dests = zip(*assigned[path])
        subsrcprefix = netaddr.cidr_merge(sources)
        subdstprefix = netaddr.cidr_merge(dests)
        assert len(subsrcprefix) == len(subdstprefix)
        assigned[path] = (subsrcprefix, subdstprefix)
    return assigned
    # TODO: implement more sophisticated volume-aware splitting
    # TODO: corner case: splitting if just one IP per src/dst?
