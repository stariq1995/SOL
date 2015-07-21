# coding=utf-8
""" Mininet topology helper
"""

from mininet.topo import Topo


def offset(val, offset):
    return str(int(val) + offset)


class mnTopo(Topo):
    """ Implements custom topology class that allows loading of panacea
    graphml files
    """

    def __init__(self, topo,**params):

        Topo.__init__(self, **params)

        for n in topo.nodes(False):
            n = offset(n, 1)  # offset in case topoliges start from 0
            # print n
            self.addSwitch(n)
            self.addHost('h{}'.format(n))
            self.addLink(n, 'h{}'.format(n))
            if topo.hasMiddlebox(n):
                self.addHost('m{}'.format(n))
                self.addLink(n, 'm{}'.format(n))

        # add links here:
        for u, v in topo.getGraph().to_undirected().edges_iter():
            self.addLink(offset(u, 1), offset(v, 1))

