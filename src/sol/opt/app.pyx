# coding=utf-8
import uuid

from varnames import ALLOCATE_FLOW, ROUTE_ALL

class App(object):
    def __init__(self, dict pptc, list constraints, dict resourceCost=None, str obj=None, objTC=None,
                 str name=''):
        self.pptc = pptc
        self.obj = obj
        self.resourceCost = resourceCost
        self.name = name
        if not self.name:
            self.name = str(uuid.uuid4()).replace('-', '')
        self.constraints = constraints
        self.objTC = objTC
        if self.objTC is None:
            self.objTC = pptc.keys()

    def uses(self, str resourceName):
        return resourceName in self.resourceCost.keys()

    def __repr__(self):
        return '<sol.App {}>'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, App) and self.name == other.name
