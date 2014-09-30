""" Mininet topology helper
"""
import networkx

from mininet.topo import Topo


class mnTopo(Topo):
    """ Implements custom topology class that allows loading of panacea
    graphml files
    """

    def __init__(self, G, **params):
        """

        :param G: a py:module:`~networkx` graph or a name of file to load
            the graph from
        :param params:
            see :py:class:`mininet.topo.Topo`
        """
        Topo.__init__(self, **params)
        if isinstance(G, str):
            G = networkx.readwrite.read_graphml(G)
        G = G.copy()
        for n in G.nodes():
            # Get rid of any sinks
            if 'superSink' in G.node[n]:
                G.remove_node(n)
        for n in G.nodes_iter():
            # Remove shortcuts from middleboxes:
            if G.node[n]['functions'] == 'middlebox':
                for m in G.successors(n):
                    G.remove_edge(n, m)
                # Add back connection to parent switch
                G.add_edge(n, G.predecessors(n)[0])

        for n in G.nodes_iter():
            if 'functions' in G.node[n]:
                if G.node[n]['functions'] == 'middlebox':
                    self.addSwitch(n)
                elif G.node[n]['functions'] == 'switch':
                    self.addSwitch(n)
                    self.addHost('h{}'.format(n))
                    self.addLink(n, 'h{}'.format(n))
                else:
                    raise Exception('Unknown node type')
            else:
                # Assume it's a switch
                self.addSwitch(n)
                self.addHost('h{}'.format(n))
                self.addLink(n, 'h{}'.format(n))

        # add links here:
        for u, v in G.to_undirected().edges_iter():
            self.addLink(u, v)


topos = {'panacea': lambda graph: mnTopo(graph)}
