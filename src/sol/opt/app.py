import json


class App:
    def __init__(self, trafficClasses=None, resources=None, obj=None, name=''):
        self.obj = obj
        self.trafficClasses = trafficClasses
        self.resources = resources

    def uses(self, resource):
        return resource in self.resources

    def getResourceNames(self):
        return self.resources.keys()

    @staticmethod
    def fromDict(dict):
        return App(dict['trafficClasses'], dict['resources'], dict['obj'], name=dict['name'])

    @staticmethod
    def fromDescription(self, appString):
        return App.fromDict(json.loads(appString))
