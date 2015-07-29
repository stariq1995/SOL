# coding=utf-8

import networkx
import requests

from sol.optimization.topology.topology import Topology


class ONOSInterface(object):
    def __init__(self, controllerHost="localhost:8181"):
        self._host = controllerHost

    def pushRoutes(self, pathToPrefix):
        resp = requests.post("http://{}/sol/install".format(self._host),
                             data={'paths': [{
                                       "nodes": path.getNodes(),
                                       "srcprefix": str(prefix[0]),
                                       "dstprefix": str(prefix[1]),
                                   } for path in pathToPrefix for prefix in pathToPrefix[path]]})
        resp.raise_for_status()

    def getTopology(self):
        resp = requests.get("http://{}/onos/v1/devices".format(self._host))
        resp.raise_for_status()
        devices = resp.json()
        resp = requests.get("http://{}/onos/v1/links".format(self._host))
        resp.raise_for_status()
        links = resp.json()

        G = networkx.Graph()
        G.add_nodes_from([x['id'] for x in devices['devices']])
        G.add_edges_from([(x['src']['device'], x['dst']['device']) for x in links['links']])

        return Topology('onosTopology', G.to_directed())


# if __name__ == "__main__":
# o = ONOSInterface()
# topo = o.getTopology("192.168.99.100:8181")
# # simple test
# resp = requests.post("http://localhost:8181/sol/install", data=json.dumps([{
#     "nodes": [1, 2, 3],
#     "srcprefix": "10.0.0.0/8",
#     "dstprefix": "10.0.0.0/8",
#     "srcport": "90",
#     "dstport": "90"
# }]), headers={"content-type": "application/json"})
# resp.raise_for_status()
