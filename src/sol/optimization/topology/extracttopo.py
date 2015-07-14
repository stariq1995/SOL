#!/usr/bin/python
import json
import httplib2
import sys
import errno
from collections import namedtuple
import networkx as nx
#import matplotlib.pyplot as plt

class Extracttopo:
    
    def __init__(self):
        self.g = nx.Graph()
        
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
        ODLDict = self.getODLTopoDict(h,controllerIP)
        # g.add_edge(1,2)
        for node1 in ODLDict.keys():
            node2 = ODLDict[node1]
            #print "%d->%d"%(self.macToNode(node1.dpid), self.macToNode(node2.dpid))
            self.g.add_edge(self.macToNode(node1.dpid), self.macToNode(node2.dpid))

        return self.g.to_directed()
    
    def main(self):
        
        
        '''for k in ODLDict.keys():
            print "%s : %s"%(k,ODLDict[k])
        '''
        self.getGraph()
        #nx.draw(self.g)
        #plt.show()
        
if __name__ == "__main__":
    topo = Extracttopo()
    topo.main()
    
    
            
        
            
        



    