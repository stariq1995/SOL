#!/usr/bin/python
import json
import httplib2
import sys
import errno
from collections import namedtuple
import networkx as nx
import matplotlib.pyplot as plt

class ExtractTopo:
    
    def __init__(self,uid='admin',password='admin',controllerIp='localhost',
                 controllerPort='8181'):
        self.odlUrl = 'http://'+controllerIp+':'+controllerPort+'/restconf/'
        self.httpreq =  httplib2.Http(".cache")
        self.httpreq.add_credentials(uid, password)
        self.controllerIp = controllerIp
        self.controllerPort = controllerPort
    
    def getJsonDataFromODL(self,obj):
        url = self.odlUrl + obj
        #print url
        resp, content = self.httpreq.request(url,'GET')
        content = json.loads(content)
        return content
        
    def parseNode(self):
        nodeobj = self.getJsonDataFromODL('operational/opendaylight-inventory:nodes/')
        nodelist={}
        nodelist = nodeobj['nodes']['node']
        allswitch=[]
        for node in nodelist:
            switch = {}
            switch['id'] = node['id']
            switch['nodeconn'] = []
            switch['flow'] = []
            node_conn_list = node['node-connector']
            for conn in node_conn_list:
                node_conn = {}
                node_conn['id'] = conn['id']
                node_conn['hosts'] = []
                if 'address-tracker:addresses' in conn:
                    hlist = conn['address-tracker:addresses']
                    for host in hlist:
                        host_info = {}
                        host_info['id'] = host['id']
                        host_info['mac'] = host['mac']
                        host_info['ip'] = host['ip']
                        node_conn['hosts'].append(host_info)
                    
                switch['nodeconn'].append(node_conn)
            allswitch.append(node_conn)
        #print allswitch
        return allswitch
    
    def parseTopology(self):
        topobj = self.getJsonDataFromODL('operational/network-topology:network-topology/')
        edgelist = (topobj['network-topology']['topology'])[0]['link']
        
        alledges=[]
        for i in edgelist:
            edge={}
            if i['link-id'].find('host') != -1:
                continue
            edge['linkid'] = i['link-id']
            edge['destnode_odl'] = i['destination']['dest-node']
            edge['dest_tp'] = i['destination']['dest-tp']
            edge['srcnode_odl'] = i['source']['source-node']
            edge['src_tp'] = i['source']['source-tp']
            edge['srcnode'] = self.getNodeNum(i['source']['source-node'])
            edge['dstnode'] = self.getNodeNum(i['destination']['dest-node']) 
            edge['srcport'] = self.getPortNum(i['source']['source-tp'])
            edge['dstport'] = self.getPortNum(i['destination']['dest-tp'])
            alledges.append(edge)
            
        return alledges
    
    def getGraph(self):
        alledges = self.parseTopology()
        G = nx.DiGraph()
        edge_list=[]
        for edge in alledges:
            edge_rev = {}
            l=[]
            u = int(edge['srcnode'])
            v = int(edge['dstnode'])
            l = (u,v,edge)
            edge_list.append(l)
            edge_rev['linkid'] = edge['linkid']
            edge_rev['destnode_odl'] = edge['srcnode_odl']
            edge_rev['dest_tp'] = edge['src_tp']
            edge_rev['srcnode_odl'] = edge['destnode_odl']
            edge_rev['src_tp'] = edge['dest_tp']
            edge_rev['dstnode'] = edge['srcnode']
            edge_rev['srcnode'] = edge['dstnode'] 
            edge_rev['dstport'] = edge['srcport']
            edge_rev['srcport'] = edge['dstport']
            l = (v,u,edge_rev)
            edge_list.append(l)
        
        G.add_edges_from(edge_list)
        return G 
        
    def getPortNum(self,id):
        l = id.split(':')
        if l[0] == 'host':
            return None
        return l[-1]
    
    def getNodeNum(self,id):
        l = id.split(':')
        if l[0] == 'host':
            return None
        return l[-1]
        
        
    def main(self):
        #self.parseNode()
        '''
        edgelist = self.parseTopology()
        for edge in edgelist:
            print edge
        '''
        G = self.getGraph()
        plt.show(nx.draw(G))
            

if __name__ == '__main__':
    topo = ExtractTopo()
    topo.main()
    
    