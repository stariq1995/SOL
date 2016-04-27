# coding=utf-8

import json

import networkx
import requests
import six

from sol.topology.topology import Topology


class ONOSInterface(object):
    """
        Wrapper that allows talking to the SOL-ONOS app over the REST interface
    """
    def __init__(self, controllerHost="localhost:8181",
                 auth=('karaf', 'karaf')):
        self._host = controllerHost
        self._auth = auth

    def push_routes(self, path_to_prefix):
        """
        Install these routes (paths/IP prefixes) using ONOS
        :param path_to_prefix:
        :return:
        """
        paths = []

        # s = time.time()
        for path in six.iterkeys(path_to_prefix):
            for prefix in path_to_prefix[path]:
                paths.append({"nodes": path.getNodes(),
                              "srcprefix": str(prefix[0]),
                              "dstprefix": str(prefix[1])})
        # print time.time() - s
        resp = requests.post("http://{}/sol/install".format(self._host),
                             data=json.dumps({'paths': paths}),
                             headers={"content-type": "application/json"},
                             auth=self._auth)
        resp.raise_for_status()

    def get_topology(self):
        """
        Fetch the topology from ONOS controller
        :return:
        """
        resp = requests.get("http://{}/onos/v1/devices".format(self._host),
                            auth=self._auth)
        resp.raise_for_status()
        devices = resp.json()
        resp = requests.get("http://{}/onos/v1/links".format(self._host),
                            auth=self._auth)
        resp.raise_for_status()
        links = resp.json()

        G = networkx.Graph()
        G.add_nodes_from([x['id'] for x in devices['devices']])
        G.add_edges_from([(x['src']['device'], x['dst']['device'],
                           {"srcport": x['src']['port'],
                            "dstport": x['dst']['port']}) for x in
                          links['links']])

        return Topology('onosTopology', G.to_directed())

    def delete_all_flows(self):
        """
        Remove all flows/intents installed by SOL
        :return:
        """
        requests.get("http://{}/sol/clear".format(self._host),
                     auth=self._auth).raise_for_status()
