#!/usr/bin/python
import urllib2
import json
import networkx as nx
from networkx.readwrite import json_graph
#import matplotlib.pyplot as plt

def device_to_num(device_list,device_name):

	chassisid=0
	for device in device_list:
		if device['id'] == device_name:
			chassisid = int(device['chassisId'])
			break
	return chassisid-1 













