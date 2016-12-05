import uuid

import numpy as np
import six

from enum import Enum
from sol.path.paths cimport PPTC


cdef class App:
    """
        Represents a single network management application. Optimizition is
        built using these applications.
    """
    def __init__(self, PPTC pptc, list constraints, dict resource_cost=None,
                 obj=None, obj_tc=None, unicode name=u'', *args, **kwargs):
        """
        Create a new application

        :param pptc: paths per traffic class
        :param list constraints: list of constraints that this application cares about.
            A constraint is either a name or a tuple which contains a name and
            parameters
        :param dict resource_cost: dictionary mapping resource names to cost per flow
        :param unicode obj: name of the objective function
        :param obj_tc: traffic classes that contribute to the objective function.
            If None, traffic classes from *pptc* are used
        :param unicode name: The name of this application. If None or empty string,
            a unique uuid will be generated as the name.
        :param args:
        :param kwargs:
        :return:

        """
        self.pptc = pptc
        # Check that the objective is either a string or a tuple
        if obj is not None:
            assert isinstance(obj, unicode) or (isinstance(obj, tuple) and
                                                isinstance(obj[0], unicode))
        self.obj = obj
        self.resourceCost = resource_cost
        self.name = name
        if self.name is None or not self.name:
            self.name = six.u(str(uuid.uuid4()).replace('-', ''))
        self.constraints = constraints
        self.objTC = obj_tc
        if self.objTC is None:
            self.objTC = list(pptc.tcs())
        self.predicate = kwargs.get('predicate')

    def uses(self, unicode resource_name):
        """
        Check wheter the application uses a particular resource.

        :param resource_name: the name of the resource
        :return: True or False
        """
        return resource_name in self.resourceCost.keys()

    def volume(self):
        """
        Computes the total amount of traffic (number of flows) that the
        application is responsible for.
        This is the sum of number of flows across all traffic classes for
        this application.

        :return: total application volume
        :rtype: float
        """
        return np.sum([np.sum(tc.volFlows) for tc in self.pptc])

    def objstr(self):
        """
        Returns the string name of this application

        :return:
        """
        if isinstance(self.obj, tuple):
            return self.obj[0]
        else:
            return self.obj

    def __repr__(self):
        return u'<sol.App {}>'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    # def __eq__(self, other):
    #     return isinstance(other, App) and self.name == other.name


class ConstraintType(Enum):
    pass


class Resource(Enum):
    pass


class Objective(Enum):
    pass


class PathPerTrafficClass(dict):
    def tcs(self):
        return six.keys(self)


class Constraint(object):
    def __init__(self, constr_type, resource):
        pass
