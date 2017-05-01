import uuid

import networkx
import numpy as np
import six

from sol.path.paths cimport PPTC

from sol.utils.const import LINKS, ERR_UNKNOWN_MODE
from sol.utils.const import NODES

cdef class App:
    """
        Represents a single network management application. A unified optimizition is
        built using these applications.
    """
    def __init__(self, PPTC pptc, constraints, resource_cost,
                 obj, obj_tc=None, unicode name=u''):
        """
        Create a new application with given paramenters

        :param pptc: paths per traffic class
        :param list constraints: list of constraints that this application cares about.
            A constraint is either a name or a tuple which contains a name and
            parameters
        :param dict resource_cost: dictionary mapping resource names to cost per flow
        :param unicode obj: name of the objective function
        :param obj_tc: traffic classes that contribute to the objective function.
            If None, traffic classes from *pptc* are used
        :param unicode name: The name of this application. If None or empty string,
            a uuid will be generated as the name.

        .. note::
            Name given serves as a unique identifier of the application
        """
        self.pptc = pptc
        # Check that the objective is either a string or a tuple
        # No longer necessary, switching to a tuple representation
        # if obj is not None:
        #     assert isinstance(obj, unicode) or (isinstance(obj, tuple) and
        #                                         isinstance(obj[0], unicode))
        self.obj = obj
        self.resource_cost = resource_cost
        self.name = name
        if self.name is None or not self.name:
            self.name = six.u(str(uuid.uuid4()).replace('-', ''))
        self.constraints = constraints
        self.obj_tc = obj_tc
        if self.obj_tc is None:
            self.obj_tc = list(pptc.tcs())

    def uses(self, unicode resource_name):
        """
        Check wheter the application uses a particular resource.

        :param resource_name: the name of the resource
        :return: True or False
        """
        return resource_name in self.resource_cost.keys()

    cpdef double volume(self):
        """
        Computes the total amount of traffic (number of flows) that the
        application is responsible for.
        This is the sum of number of flows across all traffic classes and all epochs for
        this application.

        :return: total application volume
        :rtype: float
        """
        return np.sum([np.sum(tc.volume()) for tc in self.pptc])

    # def objstr(self):
    #     """
    #     Returns the string name of this objective function
    #
    #     :return:
    #     """
    #     if isinstance(self.obj, tuple):
    #         return self.obj[0]
    #     else:
    #         return self.obj

    def __repr__(self):
        return u'<sol.App {}>'.format(self.name)

    def __hash__(self):
        return hash(self.name)

    def __richcmp__(x, y, op):
        # Two apps are the same if their names match
        if op == 2:
            return x.name == y.name
        elif op == 3:
            return x.name != y.name
        else:
            raise TypeError('Operation not supported')


class AppBuilder(object):
    """
    Build an application using chained function calls. For example:

    >>> app = AppBuilder.name('myapp').addConstr('routeall').build()
    """

    def __init__(self):
        self._name = six.u(str(uuid.uuid4()).replace('-', ''))
        self._constraints = networkx.empty_graph(create_using=networkx.DiGraph())
        self._obj = None
        self._obj_tcs = None
        self._pptc = PPTC()
        self._resource_cost = {}

        self._constr_graph = networkx.DiGraph()


    def name(self, unicode name):
        """
        Sets the application's name
        :param name: the name that identifies this application
        :returns: the builder
        """
        self._name = name
        return self

    def pptc(self, PPTC pptc):
        """
        Set the application's paths per traffic class. This sets both
        the traffic classes the application owns and the pahts per each trraffic class

        :param pptc: a pptc object (see :py:class:`sol.path.PPTC`)
        :returns: the builder
        """
        self._pptc = pptc
        return self

    def add_constr(self, name, *args, **kwargs):
        """
        Add a constraint to the application

        :param name: name of the constraint (see list of supported constraints as defined
            by :py:class:`sol.opt.OptimizationGurobi`)
        :param args: positional arguments that will be passed to the constraint function
        :param kwargs: keyword arguments that will be passed to the constraint function
        :returns: the builder
        """
        self._constraints.add_node(name, object=(args, kwargs))
        return self

    def objective(self, name, *args, **kwargs):
        """
        Set a predefined objective for this application
        :param name: the objective name
        :param args: positional arguments that will be passed to the objective function
        :param kwargs: keyword arguments that will be passed to the objective function
        """
        self._obj = (name, args, kwargs)
        return self

    def objective_tcs(self, tcs):
        """
        Use this to indicate that the set of traffic classes which contribute to the
        objective function is different from the overall traffic classes specified
        in :py:meth:`pptc`. Normally you should not need this, but if you desire
        to ignore some of the traffic classes when computing the objective function,
        this is the place to do it.

        :param tcs: a list of traffic classes that DO contribute to the objective function
        :return:
        """
        self._obj_tcs = tcs
        return self

    def add_resource(self, name, cost_func, applyto):
        """
        Indicate that this application uses a given resource,
        :param name: resource name
        :param cost_func: cost function that computes how much a
        :param applyto: either 'nodes' or 'links' to indicate whether the resource is owned by nodes
        or links in the network
        :return:
        """
        if applyto not in [NODES, LINKS]:
            raise ValueError(ERR_UNKNOWN_MODE % ('resource owner', applyto))
        self._resource_cost[name] = (cost_func, applyto)
        return self

    def build(self):
        """
        :returns: the constructed application
        :rtype: :py:class:App
        """

        # TODO: topologically sort the constraints before making the App constraints
        # self.constraints.add_edges_from(
        #     self.constr_graph.subgraph(self.constraints.nodes()).edges())
        # c = networkx.topological_sort(self.constraints)
        c = [(c, self._constraints.node[c]['object'][0], self._constraints.node[c]['object'][1])
             for c in self._constraints.nodes()]

        return App(self._pptc, c, self._resource_cost, self._obj, self._obj_tcs, self._name)
