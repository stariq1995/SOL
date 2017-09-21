import networkx as nx
import requests

from sol.sdn.translator import split_prefix


class RestException(Exception):
    pass


def default_dev_mapper(dev_id):
    return int(dev_id.lstrip('of:'))


class ONOS(object):
    def __init__(self, api_prefix='http://127.0.0.1:8181/onos/v1',
                 auth=('karaf', 'karaf'), dev_mapper=default_dev_mapper):
        self.prefix = api_prefix
        self.dev_mapper = dev_mapper
        self.dev_back = {}
        self.auth = auth
        # self.topo = self.get_topo()

    def get_topo(self):
        # Get ONOS clusters (we usually expect just 1)
        r = requests.get(self.prefix + '/topology/clusters', auth=self.auth)
        clust = r.json()
        g = nx.Graph()
        for c in clust['clusters']:
            # Get devices
            devs = requests.get(self.prefix + '/topology/clusters/{}/devices'.format(c['id']),
                                auth=self.auth).json()
            for d in devs['devices']:
                intd = self.dev_mapper(d)
                g.add_node(intd)
                self.dev_back[intd] = d
            # Get links
            links = requests.get(self.prefix + '/topology/clusters/{}/links'.format(c['id']),
                                 auth=self.auth).json()
            for l in links['links']:
                g.add_edge(*map(self.dev_mapper, (l['src']['device'], l['dst']['device'])),
                           attr_dict=dict(srcport=l['src']['port'], dstport=l['dst']['port']))

    def deploy(self, pptc):
        all_flows = []
        for tc in pptc.tcs():
            paths = pptc.paths(tc)
            ip_tuples = split_prefix(tc.srcIPprefix, tc.dstIPprefix, pptc.paths(tc))
            for p, tup in zip(paths, ip_tuples):
                s, d = tup
                for u, v in p.links():
                    all_flows.append({
                        "timeout": 0,
                        "isPermanent": True,
                        "deviceId": self.dev_back[u],
                        "treatment": {
                            "instructions": [
                                {
                                    "type": "OUTPUT",
                                    "port": self.topo.edge[u][v]['dstport']
                                }
                            ]
                        },
                        "selector": {
                            "criteria": [
                                {
                                    "type": "ETH_TYPE",
                                    "ethType": "0x8800"
                                },
                                {
                                    "type": "IPV4_SRC",
                                    "ip": s
                                },
                                {
                                    "type": "IPV4_DST",
                                    "ip": d
                                },
                            ]
                        }
                    })
                    # And last hop to host
        requests.post(self.prefix + '/flows/', json={'flows': all_flows}, auth=self.auth)
