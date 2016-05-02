# coding=utf-8
""" Mininet topology helper
"""


def offset(val, o):
    """
    Offset value of an integer in string form by o.
    :param val: value
    :param o: the offset
    :return: string representation of value+o
    """
    return str(int(val) + o)


try:
    from mininet.topo import Topo
except ImportError as e:
    print("You need mininet installed!")
    raise e


class mnTopo(Topo):
    """
    Implements custom topology class that allows loading
    graphml files
    """

    def __init__(self, topo, **params):

        Topo.__init__(self, **params)

        for n in topo.nodes(False):
            n = offset(n, 1)  # offset in case topoliges start from 0
            # print n
            self.addSwitch(n)
            self.addHost('h{}'.format(n))
            self.addLink(n, 'h{}'.format(n))
            # if topo.has_middlebox(n):
            #     self.addHost('m{}'.format(n))
            #     self.addLink(n, 'm{}'.format(n))

        # add links here:
        for u, v in topo.get_graph().to_undirected().edges_iter():
            self.addLink(offset(u, 1), offset(v, 1))
