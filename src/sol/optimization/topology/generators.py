"""
Generates toplogies for various applications we are evaluating

MUST DOCUMENT MORE
"""
import warnings
from random import shuffle, sample
import itertools

import networkx as nx

from panacea.lps.formulation.generateClasses import getClassesRegular, \
    getClassesEqual
import panacea.lps.commonConfig as cc
from panacea.lps.apps import apps
from panacea.lps.topology.topology import TestTopology


def forceSwitchLabels(topology):
    """ Force all nodes to be labeled as switches

    :param topology: topology to operate on
    :return:
    """
    G = topology.getGraph()
    for n in G.nodes_iter():
        G.node[n]['functions'] = 'switch'


def addMiddleboxes(topology, locations=None, superSink=True, shortcuts=True,
                   mtypes=None):
    """

    ..note::
        Does not provision the nodes or links

    :param topology: topology to modify
    :param locations: ids of switches to attach middleboxes to
    :param superSink: True if we should add sinks
    :param shortcuts: add links from middleboxes to switches downstream
    :param mtypes: types of middleboxes
    :return:
    :rtype :py:class:`~panacea.optimization.topology.Topology`
    """

    c = topology.__class__
    newTopo = c(topology.name, None, topology.getNumFlows())
    G = topology.getGraph().copy()

    caps = []
    for l in G.edges_iter():
        u, v = l
        if 'capacity' in G.edge[u][v]:
            caps.append(G.edge[u][v]['capacity'])
    if len(caps) > 0:
        linkcap = sum(caps) / len(caps)
    else:
        linkcap = 0
    if linkcap == 0:
        warnings.warn('linkcap=0')
    defaultLinkProp = {'capacity': linkcap, 'weight': 1}
    origNumNodes = len(G)
    newid = origNumNodes + 1
    if locations is None:
        locations = G.nodes()
    if mtypes is None:
        mtypes = [None] * len(locations)

    for ind, node in enumerate(locations):
        # Attach another node to each existing node in the topology
        mt = mtypes[ind]
        ids = []
        if not hasattr(mt, '__iter__'):
            mt = [mt]
        for m in mt:
            G.add_node(newid)
            ids.append(newid)
            # Set node type
            G.node[newid]['functions'] = 'middlebox'
            if m is not None:
                G.node[newid]['mtype'] = m
            newid += 1
        if len(ids) > 1:
            G.add_edges_from(itertools.izip(ids, ids[1:]))

        # Attach links to the middlebox
        G.add_edge(node, ids[0], attr_dict=defaultLinkProp)
        if shortcuts:  # cut through to the neighbors immediately
            for neighbor in G.neighbors(node):
                if not neighbor in ids:
                    G.add_edge(ids[-1], neighbor, attr_dict=defaultLinkProp)
        else:  # or loop back the original node
            G.add_edge(ids[-1], node, attr_dict=defaultLinkProp)

        # Add a supersink, if requested
        if superSink:
            # TODO: fix hardcoded constant
            supersinkid = origNumNodes * 10 + node
            G.add_node(supersinkid)
            G.node[supersinkid]['superSink'] = True
            G.node[supersinkid]['sinkParent'] = node
            G.add_edge(node, supersinkid, attr_dict={'weight': 1})
            G.add_edge(ids[-1], supersinkid, attr_dict={'weight': 1})

    newTopo.setGraph(G)
    return newTopo


def generateSIMPLETopology(topology):
    """
    :param topology: original topology
    :return: the new SIMPLE topology with middleboxes, provisioned links and
        nodes
    """
    conf = apps['SIMPLE']

    forceSwitchLabels(topology)
    pairs = topology.generateIEPairs(1, 1, hasSinks=False)
    try:
        tm = topology.generateTrafficMatrix(pairs, model=conf['trafficModel'])
    except ValueError:
        tm = topology.generateTrafficMatrix(pairs, model='uniform')
    topology.provisionLinks(tm, getClassesRegular(conf['resources']),
                            cc.LPconfig['overprovision'],
                            setAttr=True)
    G = topology.getGraph()
    locations = G.nodes()
    # locations = sample(G.nodes(), G.number_of_nodes() / 2)
    for n in locations:
        G.node[n]['hasmbox'] = True
    # types = [('ids', 'fw')]
    # loctypes = []
    # for typ in types:
    # loctypes.extend([typ] * int(floor(len(locations) * 1.0 / len(types))))
    # loctypes = [types[0]] * len(locations)
    # shuffle(loctypes)
    # loctypes = dict(zip(locations, loctypes))
    # topology = addMiddleboxes(topology,
    #                           locations=loctypes.keys(),
    #                           mtypes=loctypes.values())

    topology.provisionNodes(tm, getClassesRegular(conf['resources']),
                            conf['resources'], setAttr=True, nodeTypes='switch')

    G = topology.getGraph()
    # Add discrete capacities
    for node in G.nodes_iter():
        if topology.isSwitch(node):
            for r in conf['discreteResources']:
                cap = conf['{}capacity'.format(r)]
                G.node[node]['{}capacity'.format(r)] = cap(topology) \
                    if hasattr(cap, '__call__') else cap
    # print G.edges(data=True)
    # for u, v, d in G.edges(data=True):
    #     print {k:type(v) for k,v in d.iteritems()}
    return topology


def generateMerlinTopology(topology):
    """
    :param topology: original topology
    :return: the new topology with middleboxes and provisioned links
    """
    conf = apps['Merlin']
    forceSwitchLabels(topology)
    topology.provisionLinks(
        topology.generateTrafficMatrix(
            topology.generateIEPairs(1, 1, False), conf['trafficModel']),
        getClassesRegular(conf['resources']),
        cc.LPconfig['overprovision'],
        setAttr=True)
    return addMiddleboxes(topology)


def generatePanopticonTopology(topology):
    """

    :param topology:
    :return:
    """
    conf = apps['Panopticon']
    forceSwitchLabels(topology)
    topology.provisionLinks(
        topology.generateTrafficMatrix(topology.generateIEPairs(1, 1, False),
                                       conf['trafficModel']),
        getClassesRegular(conf['resources']),
        cc.LPconfig['overprovision'],
        setAttr=True)
    return topology


def generateElasticTopology(topology):
    """

    :type topology: original Topology
    :return new topology with provisioned links
    """
    forceSwitchLabels(topology)
    conf = apps['Elastic']
    provision = apps['Elastic'].get('overprovision',
                                    cc.LPconfig['overprovision'])
    topology.provisionLinks(
        topology.generateTrafficMatrix(
            topology.generateIEPairs(**conf['pairparams']),
            conf['trafficModel']),
        getClassesRegular(), provision, setAttr=True)
    return topology


def generateSWANTopology(topology):
    """
    :param topology: original topology
    :return: new SWAN topology with provisioned links
    """
    forceSwitchLabels(topology)
    conf = apps['SWAN']
    provision = conf.get('overprovision',
                         cc.LPconfig['overprovision'])
    topology.provisionLinks(
        topology.generateTrafficMatrix(
            topology.generateIEPairs(**conf['pairparams']),
            conf['trafficModel']),
        getClassesEqual(conf['trafficClasses']), provision,
        setAttr=True)
    return topology


def generateFatTree(k, numFlows=None):
    """ Creates a fattree topology as a directed graph

    :param k: specify the k-value that controls the size of the topology
    :param numFlows: optional number of flows for this network
    :returns: a networkx DiGraph
    """
    G = nx.empty_graph()
    # Let's do the pods first
    index = 1
    middle = []
    for pod in xrange(k):
        lower = xrange(index, index + k / 2)
        index += k / 2
        upper = xrange(index, index + k / 2)
        index += k / 2
        # Add upper and lower levels
        G.add_nodes_from(lower, layer='edge', functions='switch')
        G.add_nodes_from(upper, layer='aggregation', functions='switch')
        # connect the levels
        G.add_edges_from(itertools.product(lower, upper), capacitymult=1)
        # keep the upper level for later
        middle.extend(upper)
    # Now, create the core
    core = []
    for coreswitch in xrange((k ** 2) / 4):
        G.add_node(index, layer='core', functions='switch')
        core.append(index)
        index += 1
    G.add_edges_from(itertools.product(core, middle), capacitymult=10)
    G = G.to_directed()
    # Compute the number of flows for this network
    if numFlows is None:
        a = (k ** 2) / 2
        G.graph['numFlows'] = a * (a - 1) * 1000
    else:
        G.graph['numFlows'] = numFlows
    return G


def generateChainTopology(n, name='chain'):
    """
    Generates a chain topology

    :param n: number of nodes in the chain
    :param name: name of the topology
    :return: the new topology
    :rtype TestTopology
    """
    G = nx.path_graph(n).to_directed()
    t = TestTopology(name, G)
    forceSwitchLabels(t)
    return t


def generateCompleteTopology(n, name='complete'):
    """
    Generates a complete graph toplogy

    :param n: number of nodes in the complete graph
    :param name: name of the topology
    :return: the new topology
    :rtype: TestTopology
    """
    G = nx.complete_graph(n).to_directed()
    t = TestTopology(name, G)
    forceSwitchLabels(t)
    return t

