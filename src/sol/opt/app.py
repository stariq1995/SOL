class App:
    def __init__(self, trafficClasses, resources, obj):
        self.Obj = obj
        self.trafficClasses = trafficClasses
        self.resources = resources

    def uses(self, resource):
        return resource in self.resources

    def getResourceNames(self):
        return self.resources.keys()
