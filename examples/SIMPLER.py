#!/usr/bin/python

import functools
import itertools
import json
import networkx
import re
import time
from sol.optimization.formulation import getOptimization
from sol.optimization.formulation.funcs import defaultLinkFunc, defaultLinkFuncNoNormalize
from sol.optimization.path.generate import generatePathsPerTrafficClass
from sol.optimization.path.predicates import useMboxModifier
from sol.optimization.path.select import chooserand
from sol.optimization.topology import generators
from sol.optimization.topology import provisioning
from sol.optimization.topology.provisioning import generateTrafficClasses
from sol.sdn.controller_lithium import OpenDayLightController

if __name__=='__main__':
	start_time = time.time()
	topo = generators.extractTopo()
	generators.forceSwitchLabels(topo)
	
	for node,data in topo.nodes():
		topo.setMbox(node)
		topo.setServiceTypes(node,['switch','fw','ids'])
	#======Data============
	iePairs=provisioning.generateIEpairs(topo)
	#print "All Ingress-Egress pairs are :-"
	#print iePairs
	trafficMatrix=provisioning.computeUniformTrafficMatrixPerIE(iePairs, 10 ** 4)
	trafficClasses=generateTrafficClasses(iePairs,trafficMatrix,{'Everything':1},{'Everything':200},topo._graph)
	#print "All Traffic Classes :-"
	#print trafficClasses
	for t in trafficClasses:
		t.cpuCost=10
	maxCPUCap=provisioning.computeMaxIngressLoad(trafficClasses,{t:t.cpuCost for t in trafficClasses})
	#print "Maximum Node capacities = %d"%(maxCPUCap)
	nodeCaps=dict()
	nodeCaps['cpu']={node:maxCPUCap*2 for node,data in topo.nodes() if 'fw' or 'ids' in topo.getServiceTypes(node)}
	#print "All CPU Capacities :-"
	#print nodeCaps['cpu']
	nodeCaps['tcam']={node:1000 for node,data in topo.nodes()}
	#print "All Node TCAM capacities :-"
	#print nodeCaps['tcam']
	linkCaps=provisioning.provisionLinks(topo,trafficClasses,3)
	#print "Link Capacities :-"
	#print linkCaps
	
	#==========Conditions============
	
	def my_predicate(path,topology):
		return any([s==('fw','ids') for s in itertools.product(*[topology.getServiceTypes(node) for node in path.useMBoxes])])
	
	def my_NodeCapFunc(node, tc, path, resource, nodeCaps):
		if resource == 'cpu' and node in nodeCaps['cpu']:
			return tc.volFlows * tc.cpuCost / nodeCaps[resource][node]
		else:
			raise ValueError("wrong resource")
	capFunc = functools.partial(my_NodeCapFunc, nodeCaps=nodeCaps)
	
	def my_TCAMFunc(node, tc, path, resource):
        # it would be best to test if node is a switch here, but we know all nodes are switches in this scenario
		if resource == 'tcam':
			return 2  # two rules per path on each switch, as an example.
		else:
			raise ValueError("wrong resource")  # just in case

	#=====Optimization=========
	opt=getOptimization()
	pptc=generatePathsPerTrafficClass(topo,trafficClasses,my_predicate,
									  networkx.diameter(topo.getGraph())*1.5,
									  1000,functools.partial(useMboxModifier, chainLength=2))

	#print "Before choosing :-"
	#print pptc							
	
	pptc=chooserand(pptc,5)
	#print "After choosing :-"
	#print pptc
	
	opt.addDecisionVariables(pptc)
	opt.addBinaryVariables(pptc,topo,['path','node'])
	opt.addAllocateFlowConstraint(pptc)
	opt.addRouteAllConstraint(pptc)
	opt.addLinkCapacityConstraint(pptc, 'bandwidth', linkCaps, defaultLinkFuncNoNormalize)
	opt.addNodeCapacityConstraint(pptc, 'cpu', {node: 1 for node, data in topo.nodes()
                                                if 'fw' or 'ids' in topo.getServiceTypes(node)}, capFunc)
	opt.addNodeCapacityPerPathConstraint(pptc, 'tcam', nodeCaps['tcam'], my_TCAMFunc)	
	opt.setPredefinedObjective('minmaxnodeload', resource='cpu')
									  
	opt.solve()
	
	'''
	tclist=[]
	for tc,path in pptc.iteritems():
		tclist.append(tc)
		#print tc
	'''
	
	gpf=opt.getPathFractions(pptc)
	#print("Execution Time = %s secs" % (time.time() - start_time))
	odl = OpenDayLightController(graph = topo._graph, parallel=False)
	odl.pushODLPath(pptc,gpf)
	#print odl.pathDict
	'''
	pathList = odl.generateAllPaths(pptc,gpf)
	for p in pathList:
		if type(p[0]) is list:
			print p[0][0]._nodes
		else:
			print p[0]._nodes
	'''
	
	#ass = odl._computeSplit(k = tclist[0], paths = gpf[tclist[0]] , blockbits = 5, mindiff = False)
	#print ass
	
	print("Execution Time = %s secs" % (time.time() - start_time))
	'''
	r = input("Do you want to delete all flows?")
	if r=='y' :
		odl.delFlow(flowUrlList) 
	'''
	'''
	print gpf
	
	list_of_tc=[]
	list_of_paths=[]
	
	print "\nBefore optimization :-"
	for tc,paths in pptc.iteritems():
		list_of_tc.append(tc.__dict__)
		print tc	#All traffic classes
		#print gpf[tc]	#All paths for each traffic class after optimization
		#print tc.volBytes	#Number of bytes per class
		for path in paths:
			print path.encode() #path is an object of pathWithMBox
	
	
	print "\nAfter optimization :-"
	for tc,paths in pptc.iteritems():
		print tc.__dict__
		for path in gpf[tc]:
			print path.encode()
			list_of_paths.append(path.encode())
			
	json.dump(list_of_tc,open('f1.json','w'),indent=4)
	json.dump(list_of_paths,open('f2.json','w'),indent=4)
	
	tc_from_dump=json.load(open('f1.json'))
	paths_from_dump=json.load(open('f2.json'));
	
	print "Extracted from dump :-"
	for tc in tc_from_dump:
		print tc
	for paths in paths_from_dump:
		print paths
	'''
	
	
	
	
		
		
	
		
		
		
		
		
		
		
		
		
		
		
	
