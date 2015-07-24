import networkx
import httplib2
import json
from sol.optimization.topology.extracttopo import ExtractTopo
import networkx as nx
import netaddr
from collections import defaultdict
import itertools
#from threading import Thread,Lock,Condition
#import time
from multiprocessing import Process

class OpenDayLightController(object):
    
    def __init__(self, uid='admin',password='admin',
                 controllerIP='localhost',
                 controllerPort = '8181',graph=None,parallel=False):
        
        self.httpreq =  httplib2.Http(".cache")
        self.httpreq.add_credentials(uid, password)
        self.controllerIP = controllerIP
        self.controllerPort = controllerPort
        self.odlurl = 'http://'+controllerIP+':'+controllerPort+'/restconf'
        self.G = graph
        self.pathDict={}
        self.pptc={}
        self.parallel=False
        #self.maxFlows = (len(self.G.nodes()))**2 - len(self.G.nodes()) - 1
        #self.numFlows = 0
    
    def filterPaths(self,pptc,optPaths):
        for tc,path in pptc.iteritems():
            self.pptc[tc] = optPaths[tc]
        
    def generateAllPaths(self,pptc,optPaths,blockbits=5):
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
                    # print path, subsrcprefix, subdstprefix

                    #TODO: test the correctness of this better
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
    
    def pushODLPath(self,pptc,optPaths,blockbits=5,
                    installHw=True,priority=500):
        #start_time = time.time()
        paths = self.generateAllPaths(pptc, optPaths)
        if self.parallel:
            allProcs=[]
        #print 'Max number of flows = %d'%self.maxFlows
        flowId=0
        for j,p in enumerate(paths):
            
            if type(p[0]) is list:
                path = p[0][0]._nodes
            else:
                path = p[0]._nodes
            
            #ethSrc = self.G.edge[path[0]]
            print 'Path = ',path
            srcIpPrefix = p[1] 
            dstIpPrefix = p[2]
            for i,node in enumerate(path):
                flowName = 'Dipayan_Path%d_%d'%(j,i)
                srcNode = path[0]
                dstNode = path[-1]
                #TODO: Find host connected port of every node
                if node == srcNode:
                    inPort = 1
                    nodeId = self.G.edge[node][path[i+1]]['srcnode_odl']
                else:
                    inPort = self.G.edge[path[i-1]][node]['dstport']
                    nodeId = self.G.edge[node][path[i-1]]['srcnode_odl']
                    
                if node == dstNode:
                    outPort = 1
                else:
                    outPort = self.G.edge[node][path[i+1]]['srcport']
                
                #srcIpPrefix = p[1] 
                #dstIpPrefix = p[2]
                print 'Installing following rule in ',nodeId,' :-'
                print 'SRC IP = %s, DST IP = %s, Input Port = %s, Output Port = %s'%(srcIpPrefix,dstIpPrefix,inPort,outPort)
                newFlow = self.buildFlow(flowName=flowName, tableId=0, flowId=flowId, inPort=inPort, 
                                         outPort=outPort, srcNode=srcNode, dstNode=dstNode,
                                         srcIpPrefix=srcIpPrefix, dstIpPrefix=dstIpPrefix,
                                         installHw=installHw,priority=priority,nodeId=nodeId,etherType='2048')
                
                url = self.odlurl+'/config/opendaylight-inventory:nodes/node/'+nodeId+'/table/0/flow/'+str(flowId)
                flowId = flowId + 1
                #print newFlow
                #print url
                if self.parallel:
                    process = Process(target=self.putFlow,args=(url,newFlow))
                    process.start()
                    allProcs.append(process)
                else:
                    self.putFlow(url,newFlow)
        
        if self.parallel:    
            for p in allProcs:
                p.join() 
        print "Installed %d flows!"%(j+1)
        #print "Time taken to push all flows = %d"%(self.sumtime)
        #print("Execution Time = %s secs" % (time.time() - start_time))
        
    def putFlow(self,url,newFlow):
        #start_time = time.time()
        #print 'url=%s!'%url
        resp,content = self.httpreq.request(uri = url,
                                            method = 'PUT',
                                            body = json.dumps(newFlow), 
                                            headers = {'content-type' : 'application/json'})
        self.pathDict['nodeId'] = newFlow
        if resp['status'] != '200':
                    print 'Response =%s\nContent=%s'%(resp,content)
        #self.flowLock.acquire()
        #self.flowLock.release()
        #self.sumtime = self.sumtime + time.time() - start_time
        #print("%s" % (time.time() - start_time))
        #return resp,content
    
    def buildFlow(self,installHw,priority,flowName,tableId,flowId,inPort,outPort,
                  srcNode,dstNode,srcIpPrefix, dstIpPrefix, nodeId, etherType,
                  ethDst='', ethSrc=''):
        srcIpPrefix = '10.0.0.'+str(srcNode)+'/32'
        dstIpPrefix = '10.0.0.'+str(dstNode)+'/32'
        #inPort = nodeId+':'+str(inPort)
        #outPort = nodeId+':'+str(outPort)
        ethDst = '00:00:00:00:00:0'+str(dstNode)
        ethSrc = '00:00:00:00:00:0'+str(srcNode)
        newFlow = {'flow':[]}
        newFlow['flow'].append({'flow-name' : flowName,
                                'installHw' : 'true',
                                'priority' : priority,
                                'table_id' : str(tableId),
                                'id' : str(flowId),
                               #'match' : {},
                                'instructions': {'instruction' : []},
                                'strict' : 'false',
                                'cookie_mask' : '255',
                                #'hard-timeout' : '12',
                                'cookie' : '5',
                                #'idle-timeout' : '34',
                                'barrier' : 'false'})
        
        newFlow['flow'][0]['match'] = {"ethernet-match" : {'ethernet-type' : {'type' : etherType},
                                                           'ethernet-destination' : {'address' : ethDst},
                                                           'ethernet-source' : {'address' : ethSrc}
                                                          },
                                       'in-port' : str(inPort),
                                       #'ip-match' : #{'ip-protocol' : '1'
                                                     #'ip-dscp' : '2',
                                                     #'ip-ecn' : '2'
                                                    #,
                                       "ipv4-source" : srcIpPrefix,
                                       "ipv4-destination" : dstIpPrefix
                                       }
        newFlow['flow'][0]['instructions']['instruction'].append({'order' : '0',
                                                                  'apply-actions' : 
                                                                    {'action' : 
                                                                        [{'order' : '0',
                                                                          'output-action' : 
                                                                                {"output-node-connector" : str(outPort)}
                                                                                 #'max-length' : '60'}
                                                                            }
                                                                         ]
                                                                     }
                                                                  }
                                                                 )        
        return newFlow

    def getAllFlowsbyNode(self):
        url = self.odlurl+'/config/opendaylight-inventory:nodes/'
        resp,content = self.httpreq.request(uri=url, method='GET',
                                           headers = {'content-type' : 'application/json'})
        #print json.dumps(json.loads(content),indent=4)
        content = json.loads(content)
        allNodes = content['nodes']['node']
        node_flow_dict={}
        for node in allNodes:
           nodeId = node['id']
           allFlows = node['flow-node-inventory:table'] #list of dicts, each dict containing one flow
           node_flow_dict[nodeId] = allFlows
        
        return node_flow_dict
    
    def deleteAllFlows(self):
        url = self.odlurl+'/config/opendaylight-inventory:nodes/'
        resp,content = self.httpreq.request(url,'DELETE')
        #print resp,content
        if resp['status'] == '200':
            print "All flows deleted!"    
        return resp, content
    
    
    
    def main(self):
        #newFlow = self.buildFlow()
        #print json.dumps(newFlow,indent = 4)
        '''
        flows = self.getAllFlowsbyNode()
        for node in flows:
            print node,' : ',flows[node]
        ''' 
        self.deleteAllFlows()

if __name__ == "__main__":
    controller = OpenDayLightController()
    controller.main() 
        
    
    
    