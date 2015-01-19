# coding=utf-8
from abc import ABCMeta, abstractmethod
from sol.utils.pythonHelper import tup2str


class Optimization(object):
    """
        Optimization problem interface
    """
    __metaclass__ = ABCMeta

    #: Currently supported pre-defined objectives
    definedObjectives = ['maxallflow', 'maxminflow', 'minmaxnodeload',
                         'minmaxlinkload', 'minroutingcost']

    @abstractmethod
    def __init__(self):
        """
        Create a new optimization problem instance
        """


    @staticmethod
    def xp(trafficClass, pathIndex):
        """ Convenience method for formatting a decision variable

        :param trafficClass: the traffic class object, needed for the ID
        :param pathIndex: index of the path in the list of paths per traffic class
        :returns: variable name of the form *x_classid_pathindex*
        :rtype: str
        """
        return 'x_{}_{}'.format(trafficClass.ID, pathIndex)

    @staticmethod
    def al(trafficClass):
        """
        Format an allocation variable

        :param trafficClass: the traffic class object
        :return: variable name of the form *a_classid*
        """
        return 'a_{}'.format(trafficClass.ID)

    @staticmethod
    def bn(node):
        """
        Format a binary node variable

        :param node: nodeID
        :return: variable name of the form *binnode_nodeID*
        """
        return 'binnode_{}'.format(node)

    @staticmethod
    def be(head, tail):
        """
        Format a binary edge variable

        :param head: edge head (nodeID)
        :param tail: edge tail (nodeID)
        :return: variable name of the form *binedge_headID_tailID*
        """
        return 'binedge_{}_{}'.format(head, tail)

    @staticmethod
    def bp(trafficClass, pathIndex):
        """
        Format a binary path variable

        :param trafficClass: traffic class (for ID)
        :param pathIndex: path index in the list of paths per traffic class
        :return: variable name of the form *binpath_classid_pathindex*
        """
        return 'binpath_{}_{}'.format(trafficClass.ID, pathIndex)

    @staticmethod
    def nl(node, resource):
        """
        Format a node load variable

        :param node: node ID
        :param resource: the resource
        """
        return 'Load_{}_{}'.format(resource, node)

    @staticmethod
    def el(link, resource):
        """
        Format a link load variable

        :param link:
        :param resource:
        """
        return 'Load_{}_{}'.format(resource, tup2str(link))

    @staticmethod
    def nc(node, resource):
        """
        Format a capacity variable

        :param node:
        :param resource:
        """
        return 'Cap_{}_{}'.format(resource, node)

    @abstractmethod
    def solve(self):
        """
        Call the solver and solve the underlying optimization problem
        """
        pass

    @abstractmethod
    def defineVar(self, name, coeffs, const, lowerBound, upperBound):
        """
        Utility function to define an (almost) arbitrary variable.
        :param name: name of the variable
        :param coeffs: coefficients of other variables that define this
            variable, a dictionary of strings to floats.
            If None, then only the name is defined, with no value assigned
            to it.
        :param const: any non-coefficient slack
        :param lowerBound: lower bound on the variable
        :param upperBound: upper bound on the variable
        """
        pass

    @abstractmethod
    def defineVarSymbolic(self, name, symbolicEq):
        pass

    def parseSymbolicEq(self, eq):
        pass

    @abstractmethod
    def setObjectiveCoeff(self, coeffs, sense):
        """
        Set the objective coefficients for given variables

        :param coeffs: dictionary mapping variables to coefficients
        :param sense: *min* or *max* indicates whether we are minimizing or
            maximizing the objective
        """
        pass

    @abstractmethod
    def setPredefinedObjective(self, objective, resource=None):
        """
        Set a predefined objective. See :py:attr:`definedObjectives` for the list
        of supported objectives

        .. note:
            All variables must be defined before calling this function

        :param objective: predefined objective name
        :param resource: some objectives (such as minmaxnodeload) come with a
            resource parameter. Set it here.
        :raise FormulationException: if passed in objective is not supported
        """
        pass

    @abstractmethod
    def addDecisionVariables(self, pptc):
        """
        Add and set bounds on the flow fraction variables

        :param pptc: paths per commodity
        """
        pass

    @abstractmethod
    def addBinaryVariables(self, pptc, topology, types):
        """
        Add binary variables to this formulation

        :param pptc: paths per traffic class
        :param topology: the topology we are operating on
        :param types: types of binary variables to add. Allowed values are
            'node', 'edge', and 'path'
        """
        pass

    @abstractmethod
    def addRoutingCost(self, pptc, pathCostFunction):
        """
        Defines the routing cost constraint

        :param pptc: paths per traffic class
        :param pathCostFunction: User-defined function that computes the cost of the path
        """
        pass

    @abstractmethod
    def addRouteAllConstraint(self, pptc):
        """
        Add the constraint to ensure all traffic is routed

        This sets the allocation for each traffic class equal to 1.

        :param pptc: paths per traffic class
        """
        pass

    @abstractmethod
    def addAllocateFlowConstraint(self, pptc):
        """
        Allocate flow for each traffic class

        :param pptc: paths per traffic class
        """
        pass

    @abstractmethod
    def addLinkCapacityConstraint(self, pptc, resource, linkcaps, linkCapFunction):
        """
        Add a link capacity constraint

        :param pptc: paths per traffic class
        :param resource: the resource for which we are adding the capacity
            constraints
        :param linkcaps: link capacities (as a dict) mapping link IDs to capacities for this resource
        :param linkCapFunction: user defined function that computes the traffic fraction muliplier
        """
        pass

    @abstractmethod
    def addNodeCapacityConstraint(self, pptc, resource, nodecaps, nodeCapFunction):
        """
        Add a node capacity constraint

        :param pptc: paths per commodity
        :param resource: the resource for which we are adding the capacity
            constraints
        :param nodecaps: node capacities (as a dictionary) mapping node IDs to capacities for this resource
        :param nodeCapFunction: user defined function
        """
        pass

    @abstractmethod
    def addCapacityBudgetConstraint(self, resource, nodes, totCap):
        """
        Add a total capacity budget for a list of nodes and a given resource.

        To be used when the capacities are allocated by SOL, and not predefined

        :param resource: resource for which capacities are set
        :param nodes: nodes whose sum of capacities is to be capped
        :param totCap: total node capacity
        """
        pass

    @abstractmethod
    def addNodeCapacityPerPathConstraint(self, pptc, resource, nodecaps, nodeCapFunction):
        """
        Add a node capacity constraint, where capacity is consumed per path, if path is active.

        :param pptc: paths per traffic class
        :param resource: current resource
        :param nodecaps: node capacities
        :param nodeCapFunction: User-defined function that computes the traffic fraction multiplier
        """
        pass

    @abstractmethod
    def addPathDisableConstraint(self, pptc, trafficClasses=None):
        """
        Enforce disabled paths. That is, only allow traffic flow if
        the path is enabled.

        :param pptc: paths per traffic class
        :param trafficClasses: traffic classes for which this constraint
            should take effect. If None, it will be activated for all traffic classes.
        """
        pass

    @abstractmethod
    def addRequireAllNodesConstraint(self, pptc, trafficClasses=None):
        """
        Require all nodes on the path to be active for traffic to flow

        :param pptc: paths per traffic class
        :param trafficClasses: traffic classes for which this constraint should be activated.
            If None, it will be activated for all traffic classes
        """
        pass

    @abstractmethod
    def addRequireAllEdgesConstraint(self, pptc, trafficClasses=None):
        """
        Require all edges on the path to be active for traffic to flow

        :param pptc: paths per commodity
        :param trafficClasses: traffic classes for which this constraint should be activated.
            If None, it will be activated for all traffic classes
        """
        pass

    @abstractmethod
    def addRequireSomeNodesConstraint(self, pptc, trafficClasses=None, some=1):
        """
        Require at some nodes on the path to be enabled before traffic can flow along that path

        :param pptc: paths per traffic class
        :param trafficClasses: traffic classes for which this constraint should be activated.
            If None, it will be activated for all traffic classes
        :param some: how many active nodes are required. By default it's 1.
        """
        pass

    @abstractmethod
    def addBudgetConstraint(self, topology, budgetFunc, bound):
        """
        Add a budget constraint on the number of enabled nodes

        :type topology: :py:class:`~sol.optimization.topology.Topology`
        :param topology: our topology
        :param budgetFunc: a callable object that computes the cost (per node). Must be of the form::
            budgetFunc(nodeID)

        :param bound: a value that limits the cost
        :param bound: float
        """
        pass

    @abstractmethod
    def addEnforceSinglePath(self, pptc, trafficClasses=None):
        """
        Enforces a single active path per traffic class

        :param pptc: paths per traffic class
        :param trafficClasses: traffic classes for which this constraint takes effect.
            If None, all classes from *pptc* will be used.
        """
        pass

    @abstractmethod
    def addMinDiffConstraint(self, prevSolution, epsilon, diffFactor):
        """
        Add min-diff constraint. Minimizes the "distance" from the previous solution

        :param prevSolution: a dictionary containing mapping of variable names to values after the optimization
            is solved.

            Can be obtained with :py:meth:`~getAllVariableValues`
        :param epsilon: the limit on the "distance" between last solution and current solution. Must be between 0 and 1.
            If it is None, it will be inserted into the objective function in such a way that *epsilon* is minimized.
        :param diffFactor:
            If *epsilon* is None, then you must specify *diffFactor*,
            a weight of *epsilon* when it comes to the objective value.
            This value must also be between 0 and 1.

        .. note::
            For min-diff constraint to be effective, your objective function must also be normalized to be in the [0..1]
            range.
        """
        pass

    @abstractmethod
    def getPathFractions(self, pptc, flowCarryingOnly=True):
        """
        Return the solution to the problem.
        This will be a set of flow fractions per each path, which can later be transtated into rules for switches

        :param pptc: paths per traffic class
        :param flowCarryingOnly: only return flow-carrying paths (with non-zero fractions)
        :rtype: dict
        :return: dictionary, mapping path objects to fractions of flow (per traffic class)
        """
        pass

    @abstractmethod
    def getSolvedObjective(self):
        """
        Get the objective value of the solved problem

        :return: the objective value
        :rtype: float
        """
        pass

    @abstractmethod
    def getAllVariableValues(self):
        """
        Get the values of all variables in the problem.

        Must be called after problem is solved.

        :return: a dictionary of all variable values
        :rtype: dict
        """