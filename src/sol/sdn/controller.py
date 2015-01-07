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


class PanaceaController(object):
    """
        The panacea controller that manages OpenDaylight controller
    """

    def __init__(self, daylightURL='http://localhost:8080/controller/nb/v2',
                 daylightUser='admin', daylightPass='admin'):
        """
        Create a new controller
        :param daylightURL:
        :param daylightUser:
        :param daylightPass:
        :return:
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
        Returns the Daylight topology
        :return:
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

    def getFlowStats(self):
        """
        Get the flow statistics from OpenDaylight

        :return:
        """
        r = self._session.get(self._buildURL('statistics') + '/flow')
        checkErr(r)
        return r.json()

    def getRoutes(self):
        """
        Returns currently installed routes in the network
        """
        r = self._session.get(self._buildURL('flowprogrammer'))
        checkErr(r)
        return r.json()

    def pushPath(self, daylightPath, daylightGraph, srcPrefix, dstPrefix,
                 protocol=None, srcPort=None, dstPort=None, installHw=True,
                 priority=500):
        """

        :param daylightPath:
        :param daylightGraph:
        :param srcPrefix:
        :param dstPrefix:
        :param protocol:
        :param srcPort:
        :param dstPort:
        :param installHw:
        :param priority:
        :raise Exception:
        """
        props = {'installInHW': installHw,
                 'priority': priority}
        # print daylightPath
        for ind in xrange(1, len(daylightPath) - 1):
            node = daylightPath[ind]
            # print ind, node
            # print node
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
        srcprefix = netaddr.IPNetwork(k.srcprefix)
        dstprefix = netaddr.IPNetwork(k.dstprefix)
        ipbits = 32
        if srcprefix.version == 6:
            ipbits = 128
        assert blockbits <= ipbits - srcprefix.prefixlen
        assert blockbits <= ipbits - dstprefix.prefixlen
        numblocks = len(srcprefix) * len(dstprefix) / (2 ** blockbits)
        newmask1 = ipbits - blockbits
        newmask2 = ipbits - blockbits
        blockweight = 1.0 / numblocks
        assigned = defaultdict(lambda: [])
        if not mindiff:
            assweight = 0
            index = 0
            path = paths[index]
            for block in itertools.product(srcprefix.subnet(newmask1),
                                           dstprefix.subnet(newmask2)):
                assigned[path].append(block)
                assweight += blockweight
                if assweight >= path.getNumFlows():
                    # print path.getNumFlows(), assweight
                    assweight = 0
                    index += 1
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

    def generateRoutes(self, ppk, daylightGraph, blockbits=8, convertoffset=0):
        """

        :param ppk:
        :param daylightGraph:
        :param blockbits:
        :return:
        """
        routeList = []
        for k in ppk:
            numpaths = len(ppk[k])
            if numpaths > 1:
                assigned = self._computeSplit(k, ppk[k], blockbits, False)
                for path in assigned:
                    sources, dests = zip(*assigned[path])
                    subsrcprefix = netaddr.cidr_merge(sources)
                    subdstprefix = netaddr.cidr_merge(dests)
                    assert len(subsrcprefix) == 1
                    assert len(subdstprefix) == 1
                    routeList.append((convertPath(path, offset=convertoffset),
                                      daylightGraph,
                                      str(subsrcprefix[0]),
                                      str(subdstprefix[0])))
            else:
                routeList.append((convertPath(ppk[k][0], offset=convertoffset),
                                  daylightGraph,
                                  k.srcprefix, k.dstprefix))
        return routeList

    def pushRoutes(self, routeList):
        for route in routeList:
            self.pushPath(*route)

    def generateUpdatedRoutes(self, ppk, daylightGraph, blockbits=5,
                              convertoffset=0):
        """

        :param ppk:
        :param daylightGraph:
        :param blockbits:
        :return:
        """
        routeList = []
        for k in ppk:
            numpaths = len(ppk[k])
            if numpaths > 1:
                assigned = self._computeSplit(k, ppk[k], blockbits, True)
                for path in assigned:
                    sources, dests = zip(*assigned[path])
                    subsrcprefix = netaddr.cidr_merge(sources)
                    subdstprefix = netaddr.cidr_merge(dests)
                    assert len(subsrcprefix) == 1
                    assert len(subdstprefix) == 1
                    routeList.append((convertPath(path, offset=convertoffset),
                                      daylightGraph,
                                      str(subsrcprefix[0]),
                                      str(subdstprefix[0])))
            else:
                routeList.append((convertPath(ppk[k][0], offset=convertoffset),
                                  daylightGraph,
                                  k.srcprefix, k.dstprefix))
        return routeList

    def updateRoutes(self, routeList):
        # TODO: be more clever, not just delete all flows
        self.deleteAllFlows()
        self.pushRoutes(routeList)

    def getAllFlows(self):
        """
        Get all installed flows from OpenDaylight

        :return the JSON object with all flows
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
    :param path:
    :param offset: any offset when converting node numbers. Default is 0,
        but some topologies start at 0 and opendaylight craps itself. So
        offset of 1 is required
    :return:
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
    return _path


def checkErr(r):
    """
    :param r: the response recieved form the requests library
    :return True if status code is within 200s
    :raises :py:class:`~panacea.util.exceptions.ControllerException`
        If the status code is not OK (within the 200s)
    """
    if not (200 <= r.status_code < 300):
        print r.text
        raise ControllerException("REST API error, code {}".format(
            r.status_code))
    return True

# TODO: figure out hosts dynamically
