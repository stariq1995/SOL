#!/usr/bin/python

import urllib2
import json
import requests
import httplib
"""
intents_dict = json.load(urllib2.urlopen("http://192.168.56.101:8181/onos/v1/intents"))
print json.dumps(intents_dict,indent=4)
"""
'''
intents_dict = dict()
intents_data = []
intents_data.append({"state": "INSTALLED", 
            	     "details": "HostToHostIntent{id=0x10, key=0x10, appId=DefaultApplicationId{id=31, name=org.onosproject.gui}, priority=100, resources=[00:00:00:00:00:01/-1, 00:00:00:00:00:04/-1], selector=DefaultTrafficSelector{criteria=[]}, treatment=DefaultTrafficTreatment{immediate=[], deferred=[], transition=None, cleared=false, metadata=null}, constraints=[], one=00:00:00:00:00:01/-1, two=00:00:00:00:00:04/-1}", 
            "appId": "DefaultApplicationId{id=31, name=org.onosproject.gui}", 
            "type": "HostToHostIntent", 
            "id": "0x10", 
            "resources": ["00:00:00:00:00:01/-1","00:00:00:00:00:04/-1"]})


intents_dict['intents'] = intents_data
#print json.dumps(intents_dict,indent=4)

'''
intent='HostToHostIntent{id=0x1, key=0x0, appId=DefaultApplicationId{id=26, name=org.onosproject.cli}, priority=100, resources=[00:00:00:00:00:01/-1, 00:00:00:00:00:02/-1], selector=DefaultTrafficSelector{criteria=[]}, treatment=DefaultTrafficTreatment{immediate=[], deferred=[], transition=None, cleared=false, metadata=null}, constraints=[LinkTypeConstraint{inclusive=false, types=[OPTICAL]}], one=00:00:00:00:00:01/-1, two=00:00:00:00:00:02/-1}'

#r = requests.post("http://192.168.56.101:8181/onos/v1/intents",data=intent)
r=requests.delete("http://192.168.56.101:8181/onos/v1/intent/5")
print(r.status_code,r.reason)




