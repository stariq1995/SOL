# coding=utf-8
""" Implements functions necessary to operate the OpenDaylight controller
using their RESTful APIs
"""
from collections import defaultdict
import copy
import json
import re
import itertools

import networkx
import netaddr

import requests
from requests.auth import HTTPBasicAuth
from sol.utils.exceptions import ControllerException


class OpenDaylightInterface(object):
    """
        Manages OpenDaylight controller using its REST interface.
        This is a prototype implementation
    """

    def __init__(self, daylightURL='http://localhost:8080/controller/nb/v2',
                 daylightUser='admin', daylightPass='admin'):
        """
        Create a new controller

        :param daylightURL: URL to the daylight controller/namespace
        :param daylightUser: username to use when connecting. 'admin' by default
        :param daylightPass: password to use when connecting. 'admin' by default
        """
        self._baseURL = daylightURL
        self._auth = HTTPBasicAuth(daylightUser, daylightPass)
        self._session = requests.session()
        self._session.auth = self._auth
        self._defheaders = {'content-type': 'application/json'}
        self._pathmap = {}

    def _buildURL(self, service, container='default'):
        return self._baseURL + '/{}/{}'.format(service, container)

    def getTopology(self):
        """
        Returns the Daylight topology by querying the OpenDaylight controller

        :rtype: :py:class:`networkx.DiGraph`
        """

        G = networkx.DiGraph()
        r = self._session.get(self._buildURL('topology'))
        checkErr(r)
        d = r.json()
        links = []
        props = []
        for edge in d[u'edgeProperties']:
            u = edge[u'edge'][u'headNodeConnector'][u'node'][u'id']
            v = edge[u'edge'][u'tailNodeConnector'][u'node'][u'id']
            tailport = edge[u'edge'][u'tailNodeConnector'][u'id']
            headport = edge[u'edge'][u'headNodeConnector'][u'id']
            name = edge[u'properties'][u'name'][u'value']
            # print u, v, name, 'head=', headport, 'tail=', tailport
            links.append((u, v))
            props.append(
                {'tailport': tailport, 'headport': headport, 'name': name})
            # Now add the other direction
            links.append((v, u))
            props.append(
                {'tailport': headport, 'headport': tailport, 'name': name}
            )
        G.add_edges_from(links)
        for ind, (u, v) in enumerate(links):
            G.edge[u][v].update(props[ind])

        r = self._session.get(self._buildURL('switchmanager') + '/nodes')
        checkErr(r)
        d = r.json()
        for node in d['nodeProperties']:
            nodeid = node['node']['id']
            # print nodeid
            typ = node['node']['type']
            try:
                G.node[nodeid]['type'] = typ
            except KeyError:
                G.add_node(nodeid)
                G.node[nodeid]['type'] = typ

        assert networkx.is_connected(G.to_undirected())
        return G

    # def getFlowStats(self):
    #     """
    #     Get the flow statistics from OpenDaylight
    #
    #     :return:
    #     """
    #     r = self._session.get(self._buildURL('statistics') + '/flow')
    #     checkErr(r)
    #     return r.json()

    def getRoutes(self):
        """
        Returns currently installed routes in the network by querying OpenDaylight
        """
        r = self._session.get(self._buildURL('flowprogrammer'))
        checkErr(r)
        return r.json()

    def pushPath(self, daylightPath, daylightGraph, srcPrefix, dstPrefix,
                 protocol=None, srcPort=None, dstPort=None, installHw=True,
                 priority=500):
        """
        Pushes a single route to the network using the OD controller

        :param daylightPath: the route, using OpenDaylight node IDs
        :param daylightGraph: the topology, obtained from OpenDaylight (see :py:func:`getTopology`)
        :param srcPrefix: IP src prefix
        :param dstPrefix: IP dst prefix
        :param protocol: tcp/udp etc.
        :param srcPort: source ports, if any
        :param dstPort: destination ports, if any
        :param installHw: Something OpenDaylight wants. Set it to true
        :param priority: rule priority
        :raises ControllerException:
            In case OpenDaylight returns any of the non-success codes
        """
        props = {'installInHW': installHw,
                 'priority': priority}
        # print daylightPath
        for ind in xrange(1, len(daylightPath) - 1):
            node = daylightPath[ind]
            # print ind, node
            # print daylightGraph.edge[daylightPath[ind - 1]]
            ingressPort = daylightGraph.edge[daylightPath[ind - 1]][node][
                'tailport']
            egressPort = daylightGraph.edge[node][daylightPath[ind + 1]][
                'headport']
            flow_repr = 'flow_{}_{}_{}_{}_{}_{}_{}'.format(
                str(daylightPath[0]).replace(':', '').lstrip('0'),
                str(daylightPath[-1]).replace(':', '').lstrip('0'),
                ingressPort, egressPort,
                str(srcPrefix).replace('/', '.'),
                str(dstPrefix).replace('/', '.'),
                str(node).replace(':', '').lstrip('0'))
            # print flow_repr

            # print ingressPort, egressPort
            nodeType = daylightGraph.node[node]['type']
            newFlow = {'name': flow_repr, 'ingressPort': str(ingressPort),
                       'actions': ['OUTPUT=' + str(egressPort)],
                       'node': {'id': node,
                                'type': nodeType}, 'nwSrc': srcPrefix,
                       'nwDst': dstPrefix, 'etherType': '0x800'}
            if protocol is not None:
                newFlow['protocol'] = str(protocol)
            if srcPort is not None:
                newFlow['tpSrc'] = str(srcPort)
            if dstPort is not None:
                newFlow['tpDst'] = str(dstPort)
            newFlow.update(props)
            # print newFlow
            url = self._buildURL('flowprogrammer') + \
                  '/node/{}/{}/staticFlow/{}'.format(nodeType, node, flow_repr)
            # print url
            r = self._session.put(url, json.dumps(newFlow),
                                  headers=self._defheaders)
            checkErr(r)
            self._pathmap[daylightPath] = (srcPrefix, dstPrefix)

    def _computeSplit(self, k, paths, blockbits, mindiff):
        srcnet = netaddr.IPNetwork(k.srcprefix)
        dstnet = netaddr.IPNetwork(k.dstprefix)
        ipbits = 32
        if srcnet.version == 6:
            ipbits = 128
        assert blockbits <= ipbits - srcnet.prefixlen
        assert blockbits <= ipbits - dstnet.prefixlen
        numblocks = len(srcnet) * len(dstnet) / (2 ** (2 * blockbits))
        newmask1 = srcnet.prefixlen + blockbits
        newmask2 = srcnet.prefixlen + blockbits
        blockweight = 1.0 / numblocks
        assigned = defaultdict(lambda: [])
        if not mindiff:
            assweight = 0
            index = 0
            path = paths[index]
            for block in itertools.product(srcnet.subnet(newmask1),
                                           dstnet.subnet(newmask2)):
                # TODO: prettify
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
            # iteration two, use the leftover to pad paths where fractions
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
        # XXX: splitting if just one IP per src/dst?

    def generateRoutes(self, pptc, daylightGraph, blockbits=5, convertoffset=0):
        """

        :param pptc: path per traffic class obtained from the optimization
        :param daylightGraph: the openDaylight topology
        :param blockbits: How many bits define a block of IP adresses.
            The smaller the number, the more fine-grained splitting is.

        :param convertoffset: offset to use when converting paths.
            If you have topology that uses with nodeID of 0, set this to 1.
        :return:
        """
        routeList = []
        for k in pptc:
            numpaths = len(pptc[k])
            if numpaths > 1:
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
                routeList.append((convertPath(pptc[k][0], offset=convertoffset),
                                  daylightGraph,
                                  k.srcprefix, k.dstprefix))
        return routeList

    def pushRoutes(self, routeList):
        """
        Push a list of routes using REST API. (See :py:func:`generateRoutes` for route generation)

        :param routeList: list of routes/paths
        """
        for route in routeList:
            self.pushPath(*route)

    # def generateUpdatedRoutes(self, ppk, daylightGraph, blockbits=5,
    #                           convertoffset=0):
    #     """
    #
    #     :param ppk:
    #     :param daylightGraph:
    #     :param blockbits:
    #     :return:
    #     """
    #     routeList = []
    #     for k in ppk:
    #         numpaths = len(ppk[k])
    #         if numpaths > 1:
    #             assigned = self._computeSplit(k, ppk[k], blockbits, True)
    #             for path in assigned:
    #                 sources, dests = zip(*assigned[path])
    #                 subsrcprefix = netaddr.cidr_merge(sources)
    #                 subdstprefix = netaddr.cidr_merge(dests)
    #                 assert len(subsrcprefix) == 1
    #                 assert len(subdstprefix) == 1
    #                 routeList.append((convertPath(path, offset=convertoffset),
    #                                   daylightGraph,
    #                                   str(subsrcprefix[0]),
    #                                   str(subdstprefix[0])))
    #         else:
    #             routeList.append((convertPath(ppk[k][0], offset=convertoffset),
    #                               daylightGraph,
    #                               k.srcprefix, k.dstprefix))
    #     return routeList

    # def updateRoutes(self, routeList):
    #     self.deleteAllFlows()
    #     self.pushRoutes(routeList)

    def getAllFlows(self):
        """
        Get all installed flows from OpenDaylight

        :return: the JSON object with all flows
        """
        r = self._session.get(self._buildURL('flowprogrammer'))
        checkErr(r)
        return r.json()

    def deleteAllFlows(self):
        """
        Delete all installed flows in OpenDaylight

        """
        flows = self.getAllFlows()
        for f in flows['flowConfig']:
            typ = f['node']['type']
            node = f['node']['id']
            name = f['name']
            r = self._session.delete(
                self._buildURL('flowprogrammer') + '/node/{}/{}/staticFlow/{}'
                .format(typ, node, name))
            checkErr(r)


def convertPath(path, offset=0):
    """
    Convert node IDs in the path to the daylight IDs

    :param path: the path obtained from the optimization
    :param offset: An offset when converting node numbers. Default is 0,
        but some topologies start at 0 and opendaylight panics. So
        offset of 1 is required.

    """
    _path = copy.copy(path)
    for ind, node in enumerate(_path):
        if type(node) == int:
            node = hex(node + offset).lstrip('0x').zfill(16)
            _path[ind] = ':'.join(
                s.encode('hex') for s in node.decode('hex'))
        elif type(node) == str \
                and re.match(r'^([0-9A-Fa-f]{2}[:-]){5,8}([0-9A-Fa-f]{2})$',
                             node) is None:
            node = int(node) + 1
            # print node
            node = hex(node).lstrip('0x').zfill(16)
            _path[ind] = ':'.join(
                s.encode('hex') for s in node.decode('hex'))
    # print _path
    return _path


def checkErr(r):
    """
    Check the response from OpenDaylight for any error codes

    :param r: the response recieved form the requests library
    :return: True if status code is within 200s
    :raises: :py:class:`~panacea.util.exceptions.ControllerException`
        If the status code is not OK (not within the 200s)

    """
    if not (200 <= r.status_code < 300):
        print r.text
        raise ControllerException("REST API error, code {}".format(
            r.status_code))
    return True
