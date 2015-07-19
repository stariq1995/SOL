import networkx
import httplib2
import json
from sol.optimization.topology.extracttopo import ExtractTopo
import networkx as nx
from networkx.release import url

class OpenDayLightController(object):
    
    def __init__(self, uid='admin',password='admin',
                 controllerIP='localhost',
                 controllerPort = '8181'):
        
        self.httpreq =  httplib2.Http(".cache")
        self.httpreq.add_credentials(uid, password)
        self.controllerIP = controllerIP
        self.controllerPort = controllerPort
        self.odlurl = 'http://'+controllerIP+':'+controllerPort+'/restconf'
        self.topo = ExtractTopo(controllerIp = controllerIP)
        self.G = self.topo.getGraph()
        
    def generateAllPaths(self,pptc,optPaths):
        optPath=[]
        paths = []
        for tc,path in pptc.iteritems():
            paths.append(optPaths[tc][0]._nodes)
        return paths
    
    def pushODLPath(self,pptc,optPaths):
        paths = self.generateAllPaths(pptc, optPaths)
        for j,path in enumerate(paths):
            print path
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
                
                newFlow = self.buildFlow(flowName, tableId=i, flowId=j, inPort=inPort, 
                                         outPort=outPort, srcNode=srcNode, dstNode=dstNode)
                
                url = self.odlurl+'/config/opendaylight-inventory:nodes/node/'+nodeId+'/table/'+str(i)+'/flow/'+str(j)
                print url
                #print json.dumps(newFlow,indent=4)
                resp, content = self.putFlow(url,newFlow)
                #print 'Response =%s\nContent=%s'%(resp,content)
                if resp['status'] != '200':
                    print 'Response =%s\nContent=%s'%(resp,content)
                
    def putFlow(self,url,newFlow):
        resp,content = self.httpreq.request(uri = url,
                                            method = 'PUT',
                                            body = json.dumps(newFlow), 
                                            headers = {'content-type' : 'application/json'}) 
        return resp,content
    
    def buildFlow(self,flowName='blah',tableId=0,flowId=0,inPort=1,outPort=2,srcNode=1,dstNode=4):
        srcIp = '10.0.0.'+str(srcNode)+'/24'
        dstIp = '10.0.0.'+str(dstNode)+'/24'
        defaultPriority = "500"
        
        newFlow = {'flow':[]}
        newFlow['flow'].append({'flow-name' : flowName,
                                'installHw' : 'true',
                                'priority' : defaultPriority,
                                'table_id' : str(tableId),
                                'id' : str(flowId),
                               #'match' : {},
                                'instructions': {'instruction' : []},
                                'strict' : 'false',
                                'cookie_mask' : '255',
                                'hard-timeout' : '12',
                                'cookie' : '5',
                                'idle-timeout' : '34',
                                'barrier' : 'false'})
        
        newFlow['flow'][0]['match'] = {"ethernet-match" : {'ethernet-type' : {'type' : '2048'}
                                                           #'ethernet-destination' : {'address' : 'ff:ff:ff:ff:ff:ff'},
                                                           #'ethernet-source' : {'address' : 'ff:ff:ff:ff:ff:ff'}
                                                           },
                                       'in-port' : str(inPort),
                                       'ip-match' : {'ip-proto' : 'ipv4'
                                                     #'ip-dscp' : '2',
                                                     #'ip-ecn' : '2'
                                                    },
                                       "ipv4-source" : srcIp,
                                       "ipv4-destination" : dstIp
                                       }
        newFlow['flow'][0]['instructions']['instruction'].append({'order' : '0',
                                                                  'apply-actions' : 
                                                                    {'action' : 
                                                                        [{'order' : '0',
                                                                          'output-action' : 
                                                                                {"output-node-connector" : str(outPort),
                                                                                 'max-length' : '60'}
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
        newFlow = self.buildFlow()
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
        
    
    
    