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
    
        
    def Httpcon(self,uid,password):
        h = httplib2.Http(".cache")
        h.add_credentials(uid, password)
        return h

    def getODLTopoDict(self,h,controllerIP):
        odl_ip = controllerIP
        odl_port = "8080";
        request_string = "http://"+odl_ip+":"+odl_port+"/controller/nb/v2/topology/default"
        resp,content =  h.request(request_string,"GET");
        status = resp['status'];
        if status != '200':
            err_str =  'Error in HTTP GET ('+str(resp['content-location'])+') error-code:'+str(status)
            tkMessageBox.showerror("The Cable Guy", err_str)
            sys.exit(0)
            
        edgeProperties = json.loads(content)
        #print json.dumps(edgeProperties,indent=4)
        odlEdges = edgeProperties['edgeProperties']
        EdgeObject = namedtuple("EdgeObject","dpid portnum")
        ODLDict = { }
        
        for edge in odlEdges:
            ODLkey = EdgeObject(dpid = edge['edge']['headNodeConnector']['node']['id'],
                                portnum = edge['edge']['headNodeConnector']['id'])
            ODLval = EdgeObject(dpid = edge['edge']['tailNodeConnector']['node']['id'],
                                portnum = edge['edge']['tailNodeConnector']['id'])
            ODLDict[ODLkey] = ODLval
            
        return ODLDict
    
    def macToNode(self,mac):
        nums = mac.split(':')
        return int(nums[7],16) + int(nums[6],16) 
    
    def getGraph(self,controllerIP):
        h = self.Httpcon('admin','admin')
        g = nx.Graph()
        ODLDict = self.getODLTopoDict(h,controllerIP)
        #print ODLDict
        # g.add_edge(1,2)
        links=[]
        portnums = []
        names = {}
        for node1 in ODLDict.keys():
            node2 = ODLDict[node1]
            #print "%d->%d"%(self.macToNode(node1.dpid), self.macToNode(node2.dpid))
            u = self.macToNode(node1.dpid)
            v = self.macToNode(node2.dpid)
            names[str(u)] = node1.dpid
            names[str(v)] = node2.dpid
            links.append((u,v))
            portnums.append({'srcport' : int(node1.portnum), 'dstport' : int(node2.portnum)})
            links.append((v,u))
            portnums.append({'srcport' : int(node2.portnum), 'dstport' : int(node1.portnum)}) 
            #g.add_edge(self.macToNode(node1.dpid), self.macToNode(node2.dpid), {'srcport' : int(node1.portnum), 'dstport' : int(node2.portnum)})
            #g.add_edge(self.macToNode(node2.dpid), self.macToNode(node1.dpid), {'srcport' : int(node2.portnum), 'dstport' : int(node1.portnum)})
    
        g.add_edges_from(links)
        for index, (u,v) in enumerate(links):
            g.edge[u][v].update(portnums[index])
        
        for n in g.nodes():
           g.node[n].update({'mac' : names[str(n)]})
           
        return g
    
    def main(self):
        
        
        '''for k in ODLDict.keys():
            print "%s : %s"%(k,ODLDict[k])
        '''
        g=self.getGraph('localhost')
        #print g.edges(data=True)
        
        allEdges = g.edges(data=True)
        for edge in allEdges:
            print "Source = %d, Destination = %d, Source Port= %d, Destination Port = %d"%(edge[0],edge[1],edge[2]['srcport'],edge[2]['dstport'])
        nx.draw(g)
        plt.show()
        
if __name__ == "__main__":
    topo = ExtractTopo()
    topo.main()
    
    
            
        
            
        



    