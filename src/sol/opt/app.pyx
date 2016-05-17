# coding=utf-8

import uuid

import numpy as np


class App(object):
    """
        Represents a single network management application. Optimizition is build
        using these applications.
    """
    def __init__(self, dict pptc, list constraints, dict resource_cost=None,
                 obj=None, obj_tc=None, str name='', *args, **kwargs):
        self.pptc = pptc
        if obj is not None:
            assert isinstance(obj, str) or (isinstance(obj, tuple) and
                                            isinstance(obj[0], str))
        self.obj = obj
        self.resourceCost = resource_cost
        self.name = name
        if not self.name:
            self.name = str(uuid.uuid4()).replace('-', '')
        self.constraints = constraints
        self.objTC = obj_tc
        if self.objTC is None:
            self.objTC = pptc.keys()
        self.predicate = kwargs.get('predicate')

    def uses(self, str resource_name):
        return resource_name in self.resourceCost.keys()

    def volume(self):
        return sum([np.sum(tc.volFlows) for tc in self.pptc])

    def objstr(self):
        if isinstance(self.obj, tuple):
            return self.obj[0]
        else:
            return self.obj

    def __repr__(self):
        return '<sol.App {}>'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, App) and self.name == other.name
