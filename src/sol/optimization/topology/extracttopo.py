#!/usr/bin/python
import json
import httplib2
import sys
import errno
from collections import namedtuple
import networkx as nx
import matplotlib.pyplot as plt
#import time

class ExtractTopo:
    
    def __init__(self,uid='admin',password='admin',controllerIp='localhost',
                 controllerPort='8181'):
        self.odlUrl = 'http://'+controllerIp+':'+controllerPort+'/restconf/'
        self.httpreq =  httplib2.Http(".cache")
        self.httpreq.add_credentials(uid, password)
        self.controllerIp = controllerIp
        self.controllerPort = controllerPort
        self.topoDataODL = {}
        self.nodeDataODL = {}
    
    def getTopoDataFromODL(self):
        url = self.odlUrl + 'operational/network-topology:network-topology/'
        #print url
        resp, content = self.httpreq.request(url,'GET')
        self.topoDataODL = json.loads(content)

    def getNodeDataFromODL(self):
        url = self.odlUrl + 'operational/opendaylight-inventory:nodes/'
        resp, content = self.httpreq.request(url,'GET')
        self.nodeDataODL = json.loads(content)
        
    def parseNode(self):
        #nodeobj = self.getTopoDataFromODL()
        self.getNodeDataFromODL()
        nodelist={}
        nodelist = self.nodeDataODL['nodes']['node']
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
    
    def parseHosts(self):
        hostList = []
        #print json.dumps(self.topoDataODL,indent=4)
        nodelist = (self.topoDataODL['network-topology']['topology'])[0]['node']
        
        for node in nodelist:
            host={}
            host['id'] = node['node-id']
            if host['id'].find('host') == -1 :
                continue
            host['ip'] = node["host-tracker-service:addresses"][0]['ip']
            host['toSwitch'] = self.getNodeId(node["host-tracker-service:attachment-points"][0]['tp-id'])
            host['toSwitchPort'] = self.getPortNum(node["host-tracker-service:attachment-points"][0]['tp-id'])
            host['mac'] =  node["host-tracker-service:addresses"][0]['mac']
            hostList.append(host)
        return hostList
            
    def getNodeId(self,id):
        temp = id.split(':')
        return temp[0]+':'+temp[1]
    
    def getIPPrefix(self,nodeId,hostList):
        hosts = self.getAllHostsOfSwitch(nodeId, hostList)
        hostIp = []
        ipPrefix = '0.0.0.0/0'
        cidr = 32
        for host in hosts:
            ip = host['ip']
            hostIp.append(ip)
            temp = ip.split('.')
            if int(temp[0]) >= 0 and int(temp[0]) < 128:
                if cidr > 8:
                    cidr = 8
                    ipPrefix = temp[0]+'.0.0.0/'+str(cidr)
            elif int(temp[0]) >= 128 and int(temp[0]) < 192:
                if cidr > 16:
                    cidr = 16
                    ipPrefix = temp[0]+'.'+temp[1]+'.0.0/'+str(cidr)
            elif int(temp[0]) >= 192 and int(temp[0]) < 224:
                if cidr > 24:
                    cidr = 24
                    ipPrefix = temp[0]+'.'+temp[1]+'.'+temp[2]+'.0/'+str(cidr)
        return ipPrefix
        
    def getAllHostsOfSwitch(self,nodeId,hostList):
        attachedHostList = []
        for host in hostList:
            if host['toSwitch'] == nodeId:
                attachedHostList.append(host)
        return attachedHostList
    
    def parseTopology(self):
        self.getTopoDataFromODL()
        #print json.dumps(topobj,indent=4)
        edgelist = (self.topoDataODL['network-topology']['topology'])[0]['link']
        hostList = self.parseHosts()
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
            edge['srcIPPrefix'] = self.getIPPrefix(edge['srcnode_odl'], hostList)
            edge['dstIPPrefix'] = self.getIPPrefix(edge['destnode_odl'], hostList)
            alledges.append(edge)
            
        return alledges
    
    def getGraph(self):
        #start_time = time.time()
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
            edge_rev['srcIPPrefix'] = edge['dstIPPrefix']
            edge_rev['dstIPPrefix'] = edge['srcIPPrefix']
            l = (v,u,edge_rev)
            edge_list.append(l)
        
        G.add_edges_from(edge_list)
        #print("Execution Time = %s secs" % (time.time() - start_time))
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
        #G = self.getGraph()
        #plt.show(nx.draw(G))
        #self.parseTopology()
        #self.getTopoDataFromODL()
        #hostList = self.parseHosts()
        #self.getIPPrefix('openflow:1', hostList)
        
        
            

if __name__ == '__main__':
    topo = ExtractTopo()
    topo.main()
    
    