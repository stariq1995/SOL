from abc import ABCMeta, abstractmethod


class Optimization(object):
    """
        Optimization problem interface
    """
    __metaclass__ = ABCMeta

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
    def setPredefinedObjective(self, objective, resource):
        """
        Set a predefined objective. See :py:attr:`definedObjectives` for the list
        of supported objectives

        .. note:
            All variables must be defined before calling this function

        :param objective: predefined objective name
        :param resource: some objectives (such as minmaxnodeload) come with a
            resource parameter. Set it here.
        :raise FormulationException: if passed objective is not supported
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
        Adds the constraint to ensure all traffic is routed

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
        Add node capacity constraints

        :param pptc: paths per commodity
        :param resource: the resource for which we are adding the capacity
            constraints
        :param linkcaps:
        :param linkCapFunction: user defined function that computes the traffic fraction muliplier
        """
        pass

    @abstractmethod
    def addNodeCapacityConstraint(self, pptc, resource, nodecaps, nodeCapFunction):
        """
        Add node capacity constraints

        :param pptc: paths per commodity
        :param resource: the resource for which we are adding the capacity
            constraints
        :param nodecaps:
        :param nodeCapFunction: user defined function
        """
        pass



    @abstractmethod
    def addNodeCapacityIfActive(self, pptc, resource, nodecaps, nodeCapFunction):
        """
        Add node capacity constraints, if the path is active.

        :param pptc: paths per traffic class
        :param resource: current resource
        :param nodecaps: node capacities
        :param nodeCapFunction: User-defined function that computes the traffic fraction multiplier
        """
        pass

    @abstractmethod
    def addPathDisableConstraint(self, pptc, trafficClasses=None):
        """
        Add *enforcePathDisable* constraint. That is, only allow traffic flow if
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
    def addRequireSomeNodesConstraint(self, pptc, trafficClasses, pathFunc):
        """
        Require at some nodes on the path to be enabled before traffic can flow along that path

        :param pptc: paths per traffic class
        :param trafficClasses: traffic classes for which this constraint should be activated.
            If None, it will be activated for all traffic classes
        :param pathFunc: User-defined function
        """
        pass

    @abstractmethod
    def addBudgetConstraint(self, topology, budgetFunc, bound):
        """
        Add a budget constraint on the number of enabled nodes

        :type topology: :py:class:`~sol.optimization.topology.Topology`
        :param topology: topology
        :param budgetFunc:
        :param bound:
        """
        # TODO: finish documenting this
        pass

    @abstractmethod
    def addEnforceSinglePath(self, pptc, trafficClasses):
        """
        :param self.cplexprob:
        :param pptc:
        """
        pass

    @abstractmethod
    def addMinDiffConstraint(self, prevSolution, epsilon, diffFactor):
        """
        :param self.cplexprob:
        :param prevSolution:
        :param epsilon:
        :param diffFactor:
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
        :return: the objective value
        :rtype: float
        """
        pass

    @abstractmethod
    def getAllVariableValues(self):
        """

        :return: a dictionary of all variable values
        :rtype: dict
        """