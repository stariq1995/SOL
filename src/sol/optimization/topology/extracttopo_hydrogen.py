#!/usr/bin/python

'''
Extracting Opendaylight(Helium) Topology
'''
import json
import httplib2
import sys
import errno
from collections import namedtuple
import networkx as nx
import matplotlib.pyplot as plt

class ExtractTopo:
    
        
    def __init__(self,uid='admin',password='admin',controllerIp='localhost',
                 controllerPort='8080'):
        self.odlUrl = 'http://'+controllerIp+':'+controllerPort+'/controller/nb/v2'
        self.httpreq =  httplib2.Http(".cache")
        self.httpreq.add_credentials(uid, password)
        self.controllerIp = controllerIp
        self.controllerPort = controllerPort
        self.topoDataODL = {}
        self.nodeDataODL = {}
        self.hostDataODL = {}
        

    def getTopoDataFromODL(self):
        request_string = self.odlUrl+"/topology/default"
        resp,content =  self.httpreq.request(request_string,"GET");
        status = resp['status'];
        if status != '200':
            err_str =  'Error in HTTP GET ('+str(resp['content-location'])+') error-code:'+str(status)
            tkMessageBox.showerror("SOL Topology Extraction Error", err_str)
            sys.exit(0)
        content = json.loads(content)
        content = content['edgeProperties']
        self.topoDataODL = content
            
            
    def getNodeDataFromODL(self):
        url = self.odlUrl + '/switchmanager/default/nodes'
        resp, content = self.httpreq.request(url,'GET')
        content = json.loads(content)
        content = content['nodeProperties']
        self.nodeDataODL = content
        return content
    
    def getHostDataODL(self):
        url = self.odlUrl + '/hosttracker/default/hosts/active/'
        resp, content = self.httpreq.request(url,'GET')
        content = json.loads(content)
        content = content['hostConfig']
        self.hostDataODL = content
    
    def parseNodes(self):
        nodeList = []
        self.getNodeDataFromODL()
        for n in self.nodeDataODL:
            node={}
            node['name'] = n['node']['type']+'|'+n['node']['id']
            node['mac'] = n['properties']['macAddress']['value']
            nodeList.append(node)
        return nodeList
    
    def parseHosts(self):
        hostList = []
        self.getHostDataODL()
        for h in self.hostDataODL:
            host = {}
            host['mac'] = h['dataLayerAddress']
            host['toSwitch'] = h['nodeType']+'|'+h['nodeId']
            host['toSwitchPort'] = h['nodeConnectorId']
            host['ip'] = h['networkAddress']
            hostList.append(host)
        return hostList
    
    def getAllHostsOfSwitch(self,nodeId,hostList):
        attachedHostList = []
        for host in hostList:
            if host['toSwitch'] == nodeId:
                attachedHostList.append(host)
        return attachedHostList
    
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
    
    def parseTopology(self):
        self.getTopoDataFromODL()
        #print json.dumps(topobj,indent=4) 
        hostList = self.parseHosts()
        alledges=[]
        for i in self.topoDataODL:
            edge={}
            
            #if i['link-id'].find('host') != -1:
             #   continue
            #edge['linkid'] = i['link-id']
            edge['destnode_odl'] = i['edge']['tailNodeConnector']['node']['type'] + '|'+\
                                    i['edge']['tailNodeConnector']['node']['id']
            #edge['dest_tp'] = i['destination']['dest-tp']
            edge['srcnode_odl'] = i['edge']['headNodeConnector']['node']['type'] + '|'+\
                                    i['edge']['headNodeConnector']['node']['id']
            #edge['src_tp'] = i['source']['source-tp']
            edge['srcnode'] = self.macToNode(i['edge']['headNodeConnector']['node']['id'])
            edge['dstnode'] = self.macToNode(i['edge']['tailNodeConnector']['node']['id']) 
            edge['srcport'] = i['edge']['headNodeConnector']['id']
            edge['dstport'] = i['edge']['tailNodeConnector']['id'] 
            edge['srcIPPrefix'] = self.getIPPrefix(edge['srcnode_odl'], hostList)
            edge['dstIPPrefix'] = self.getIPPrefix(edge['destnode_odl'], hostList)
            edge['srcNodeHostList'] = self.getAllHostsOfSwitch(edge['srcnode_odl'], hostList)
            edge['dstNodeHostList'] = self.getAllHostsOfSwitch(edge['destnode_odl'], hostList)
            
            alledges.append(edge)
            
        return alledges
    
    def macToNode(self,mac):
        nums = mac.split(':')
        return int(nums[7],16) + int(nums[6],16) 
    
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
            #edge_rev['linkid'] = edge['linkid']
            edge_rev['destnode_odl'] = edge['srcnode_odl']
            #edge_rev['dest_tp'] = edge['src_tp']
            edge_rev['srcnode_odl'] = edge['destnode_odl']
            #edge_rev['src_tp'] = edge['dest_tp']
            edge_rev['dstnode'] = edge['srcnode']
            edge_rev['srcnode'] = edge['dstnode'] 
            edge_rev['dstport'] = edge['srcport']
            edge_rev['srcport'] = edge['dstport']
            edge_rev['srcIPPrefix'] = edge['dstIPPrefix']
            edge_rev['dstIPPrefix'] = edge['srcIPPrefix']
            edge_rev['srcNodeHostList'] = edge['dstNodeHostList']
            edge_rev['dstNodeHostList'] = edge['srcNodeHostList']
            l = (v,u,edge_rev)
            edge_list.append(l)
        
        G.add_edges_from(edge_list)
        #print("Execution Time = %s secs" % (time.time() - start_time))
        return G 
        
    
    def main(self):
        
        g=self.getGraph()
        #print g.edges(data=True)
        
        allEdges = g.edges(data=True)
        for edge in allEdges:
            print edge
        nx.draw(g)
        plt.show()
        '''
        #self.getNodeDataFromODL()
        #self.getHostDataODL()
        #self.getTopoDataFromODL()
        #print json.dumps(self.nodeDataODL,indent=4)
        print self.parseHost()
        '''
        
if __name__ == "__main__":
    topo = ExtractTopo()
    topo.main()
    
    
            
        
            
        



    