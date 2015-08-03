""" Implements functions necessary to operate the OpenDaylight Lithium
controller using their RESTful APIs
"""
import httplib2
import json
#import networkx as nx
import netaddr
from collections import defaultdict
import itertools
#from threading import Thread,Lock,Condition
#import time
from multiprocessing import Process
from sol.optimization.topology.extracttopo_hydrogen import ExtractTopo

class OpenDayLightController(object):
    
    def __init__(self, uid='admin',password='admin',
                 controllerIP='localhost',
                 controllerPort = '8080',graph=None,parallel=False):
        """
        Create a new controller

        :param uid: User ID required to log into OpenDayLight. 'admin' by default.
        :param password: Password User ID required to log into OpenDayLight. 'admin' by default.
        :param controllerIP: IP Address of OpenDayLight controller.
        :param controllerPort: Port number in which controller is listening.
        :param graph: Networkx graph object representing the entire topology.
        :param parallel: Parallel processing of PUT requests enable/disable.
        """
        
        self.httpreq =  httplib2.Http(".cache")
        self.httpreq.add_credentials(uid, password)
        self.controllerIP = controllerIP
        self.controllerPort = controllerPort
        self.odlUrl = 'http://'+controllerIP+':'+controllerPort+'/controller/nb/v2'
        self.G = graph
        self.pptc={}
        self.parallel=False
        self.pathToJsonFile = '/tmp/flows.json'
    
    def filterPaths(self,pptc,optPaths):
        '''
        Filter the optimized paths per traffic class.
        :param pptc: Dictionary of all paths represented as values for traffic classes as keys.
        :param optPaths: all optimized paths per traffic class.
        
        Returns a dict of Traffic Class as keys and corresponding optimized paths as values.
        '''
        for tc,path in pptc.iteritems():
            self.pptc[tc] = optPaths[tc]
        
    def generateAllPaths(self,pptc,optPaths,blockbits=5):
        '''
        Generate a path list containing all paths to be installed in ODL.
        :param pptc: Dictionary of all paths represented as values for traffic classes as keys.
        :param optPaths: all optimized paths per traffic class.
        '''
        pathList = []
        self.filterPaths(pptc,optPaths)
        pptc = self.pptc
        for tc in pptc:
            numpath = len(pptc[tc])
            if numpath <= 1:
                pathList.append((pptc[tc],tc.srcIPPrefix,tc.dstIPPrefix))
            else:
                assigned = self._computeSplit(tc, pptc[tc], blockbits, False)
                for path in assigned:
                    sources, dests = zip(*assigned[path])
                    subsrcprefix = netaddr.cidr_merge(sources)
                    subdstprefix = netaddr.cidr_merge(dests)
                    assert len(subsrcprefix) == len(subdstprefix)
                    for s, d in itertools.izip(subsrcprefix, subdstprefix):
                        pathList.append((path,str(s), str(d)))
        
        return pathList
        
    def _computeSplit(self, k, paths, blockbits, mindiff):
        srcnet = netaddr.IPNetwork(k.srcIPPrefix)
        dstnet = netaddr.IPNetwork(k.dstIPPrefix)
        # Diffenrent length of the IP address based on the version
        ipbits = 32
        if srcnet.version == 6:
            ipbits = 128
        # Set up our blocks. Block is a pair of src-dst prefixes
        assert blockbits <= ipbits - srcnet.prefixlen
        assert blockbits <= ipbits - dstnet.prefixlen
        numblocks = len(srcnet) * len(dstnet) / (2 ** (2 * blockbits))
        #print "Number of blocks = ",numblocks
        newmask1 = srcnet.prefixlen + blockbits
        newmask2 = srcnet.prefixlen + blockbits
        blockweight = 1.0 / numblocks # This is not volume-aware
        assigned = defaultdict(lambda: [])
        if not mindiff:
            # This is the basic version, no min-diff required.
            assweight = 0
            index = 0
            path = paths[index]
            # Iterate over the blocks and pack then into paths
            for block in itertools.product(srcnet.subnet(newmask1),
                                           dstnet.subnet(newmask2)):
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
                #oldsrc, olddst = self._pathmap[p]
                oldweight = len(oldsrc) * len(olddst) / (2 ** blockbits)
                if p.getNumFlows() < oldweight:
                    assweight = 0
                    for block in itertools.product(oldsrc.subnet(newmask1),
                                                   olddst.subnet(newmask2)):
                        assigned[p].append(block)
                        assweight += blockweight
                        if assweight >= p.getNumFlows():
                            leftovers.append(block)
            # iteration two, use the leftovers to pad paths where fractions
            # are too low
            for p in paths:
                #oldsrc, olddst = self._pathmap[p]
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
    
    
    def writeJsonPath(self,pptc,optPaths,blockbits=5,
                    installHw=True,priority=500,method='REST'):
        
        '''
        Writing all the paths from generated path list into a JSON file to be
        used by ODL's JAVA app or installing the flows directly into ODL
        using its REST API.
        :param pptc: Dictionary of all paths represented as values for traffic classes as keys.
        :param optPaths: all optimized paths per traffic class.
        :param installHw: Whether the path is to be installed in the switches.
        :param priority: Flow priority. Default value is 500.
        :param method: The method by which flow needs to be installed. 
               Eg:- If method = 'REST', Flows will be installed using REST API.
                   If method = "JAVA", flows will be installed using the 
                   JAVA app. 
        '''
        #Generating all the paths to be installed.
        paths = self.generateAllPaths(pptc, optPaths)
        
        flowList = []
        flowId=0
        for p in paths:
            # Storing path in path variable.
            #Example: path = [1,3,2]
            if type(p[0]) is list:
                path = p[0][0]._nodes
            else:
                path = p[0]._nodes
            
            #Storing source and destination IP addresses and nodes.
            srcIpPrefix = p[1] 
            dstIpPrefix = p[2]
            srcNode = path[0]
            dstNode = path[-1]
            
            #Fetching source and destination MAC addresses for the particular path.
            #Fetching port number list of all ports of the source and destination
            #nodes where hosts are attached.
            srcMacList=[]
            dstMacList = []
            for host in self.G.edge[srcNode][path[1]]['srcNodeHostList'] :
                    srcMacPortList.append((host['mac'],host['toSwitchPort']))
            for host in self.G.edge[path[-2]][dstNode]['dstNodeHostList'] :
                    dstMacPortList.append((host['mac'],host['toSwitchPort']))
        
            for i,node in enumerate(path):
                flowName = 'Dipayan_Path%d'%(flowId)
                
                #Extracting source and destination nodeId's from Graph.
                if node == srcNode:
                    nodeId = self.G.edge[node][path[i+1]]['srcnode_odl']
                    
                else:
                    inPort = self.G.edge[path[i-1]][node]['dstport']
                    nodeId = self.G.edge[node][path[i-1]]['srcnode_odl']
                    
                if node != dstNode:
                    outPort = self.G.edge[node][path[i+1]]['srcport']
                
                #Installing different rules for different source and dest MAC
                #address list
                for ethSrc,srcHostPort in srcMacPortList:
                    for ethDst,dstHostPort in dstMacPortList:
                        #print 'Installing following rule in ',nodeId,' :-'
                        #print 'SRC IP = %s, DST IP = %s, Input Port = %s, Output Port = %s'%(srcIpPrefix,dstIpPrefix,inPort,outPort)
                        if node == srcNode:
                            inPort = srcHostPort
                        if node == dstNode:
                            outPort = dstHostPort
                        
                        if method == 'JAVA':
                            newFlow = self.buildFlow(flowName=flowName, 
                                                     tableId=0, 
                                                     flowId=flowId, 
                                                     inPort=inPort, 
                                                     outPort=outPort, 
                                                     ethSrc=ethSrc, 
                                                     ethDst=ethDst,
                                                     srcIpPrefix=srcIpPrefix, 
                                                     dstIpPrefix=dstIpPrefix,
                                                     installHw=installHw,
                                                     priority=priority,
                                                     nodeId=nodeId,
                                                     etherType='2048')
                            flowList.append(newFlow)
                            
                        elif method == 'REST':
                            newFlow = self.buildFlowForREST(flowName=flowName, 
                                                            tableId=0, 
                                                            flowId=flowId, 
                                                            inPort=inPort, 
                                                            outPort=outPort, 
                                                            ethSrc=ethSrc, 
                                                            ethDst=ethDst,
                                                            srcIpPrefix=srcIpPrefix, 
                                                            dstIpPrefix=dstIpPrefix,
                                                            installHw=installHw,
                                                            priority=priority,
                                                            nodeId=nodeId,
                                                            etherType=0x800)
                            self.postFlow(newFlow)
                        flowId = flowId + 1
        
        #Dumping the entire flow list in json format in a file on disk
        if method == 'JAVA':
            f = open(self.pathToJsonFile,'w')
            json.dump(flowList,f,indent=4)
            f.close()
        else:
            print "%d flows installed!"%(flowId+1)
            
    def buildFlow(self,installHw,priority,flowName,tableId,flowId,inPort,outPort,
                  ethSrc,ethDst,srcIpPrefix, dstIpPrefix, nodeId, etherType):
        '''
        This function is used to build a flow dictionary with all necessary
        parameters. This dictionary is used for dumping the flows into JSON
        file.
        '''
        newFlow = {}
        newFlow['installHw'] = installHw
        newFlow['priority'] = priority
        newFlow['flowName'] = flowName
        newFlow['flowId'] = flowId
        newFlow['inPort'] = inPort
        newFlow['outPort'] = outPort
        newFlow['ethSrc'] = ethSrc
        newFlow['ethDst'] = ethDst
        newFlow['srcIpPrefix'] = srcIpPrefix
        newFlow['dstIpPrefix'] = dstIpPrefix
        newFlow['nodeId'] = nodeId
        newFlow['etherType'] = etherType
        #newFlow['cookie'] = '5'
        
        return newFlow
    
    def buildFlowForREST(self,installHw,priority,flowName,tableId,flowId,inPort,outPort,
                  ethSrc,ethDst,srcIpPrefix, dstIpPrefix, nodeId, etherType):
        
        '''
        This function is used to build a flow dictionary with all necessary
        parameters. This dictionary is used for installing the flows directly
        using REST API.
        '''
        
        newFlow = {}
        node={}
        
        parts = nodeId.split('|')
        newFlow = {'installInHw':'true'}
        newFlow.update({'name' : flowName})
        newFlow.update({'node' : {'type' : parts[0], 'id' : parts[1]}})
        newFlow.update({'ingressPort' : inPort, 'priority' : priority})
        newFlow.update({'nwDst' : dstIpPrefix, 'nwSrc' : srcIpPrefix})
        newFlow.update({'actions':['OUTPUT=%s'%str(outPort)]})
        newFlow.update({'etherType': '0x800'})
        newFlow.update({'dlDst' : ethDst, 'dlSrc' : ethSrc})
        
        return newFlow
    
    def postFlow(self,newFlow):
        '''
        This function is used to install all the flows in ODL using its REST
        API by using HTTP 'POST' method.
        '''
        
        nodeid = newFlow['node']['id']
        fname = newFlow['name']
        url = self.odlUrl + '/flowprogrammer/default/node/OF/' + nodeid + '/staticFlow/' + fname
        #print url
        resp,content = self.httpreq.request(uri = url,
                                            method = 'PUT',
                                            body = json.dumps(newFlow), 
                                            headers = {'content-type' : 'application/json'})
        
        #Error condition
        if resp['status'] != '201' and resp['status'] != '200':
            print 'Response =%s\nContent=%s'%(resp,content)
            
    
    def deleteAllFlows(self):
        
        '''
        This function is used to delete all flows that have been installed in
        ODL using its REST API.
        '''
        
        topo = ExtractTopo()
        nodelist = topo.getNodeDataFromODL()
        
        for node in nodelist:
            nodeid = node['node']['id']
            url = 'http://localhost:8080/controller/nb/v2/flowprogrammer/default/node/OF/' + nodeid
            print url
            resp, content = self.httpreq.request(url, "GET")
            allFlows = json.loads(content)
            flows = allFlows['flowConfig']
            # Delete all flows
            for fs in flows:
                # Deleting flows
                flowname = fs['name']
                del_url = url + '/staticFlow/' + flowname
                resp, content = self.httpreq.request(del_url, "DELETE")
                
        print "All flows deleted!"
    
    def main(self):
        #newFlow = self.buildFlow()
        #print json.dumps(newFlow,indent = 4)
        '''
        flows = self.getAllFlowsbyNode()
        for node in flows:
            print node,' : ',flows[node]
        
        self.deleteAllFlows()
        '''

if __name__ == "__main__":
    controller = OpenDayLightController()
    controller.main() 
        
    
    
    
