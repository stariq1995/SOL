import uuid

from varnames import ALLOCATE_FLOW, ROUTE_ALL

class App:
    def __init__(self, dict pptc=None, dict resourceNames=None, str obj=None, objTC=None,
                 list constraints=[ALLOCATE_FLOW, ROUTE_ALL], str name=''):
        self.obj = obj
        self.pptc = pptc
        self.resourceNames = resourceNames
        self.name = name
        if not self.name:
            self.name = str(uuid.uuid4()).replace('-', '')
        self.constraints = constraints
        self.objTC = objTC
        if self.objTC is None:
            self.objTC = pptc.keys()

    def uses(self, str resourceName):
        return resourceName in self.resourceNames

    def getResourceNames(self):
        return self.resourceNames.keys()

    def __repr__(self):
        return '<sol.App {}>'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, App) and self.uuid == other.uuid
