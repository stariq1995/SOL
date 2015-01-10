SOL's APIs
==========

High-level API
--------------

.. py:currentmodule:: sol.optimization.formulation
.. autofunction:: getOptimization
.. autofunction:: kickStartOptimization

.. py:currentmodule:: sol.optimization.formulation.optbase
.. py:class:: Optimization

    .. automethod:: solve
    .. automethod:: getSolvedObjective
    .. automethod:: getPathFractions
    .. automethod:: getAllVariableValues

Mid-level API
-------------

You can programmatically "build" your optimization using the defined functions and constraints.

.. py:currentmodule:: sol.optimization.formulation.optbase

.. autoclass:: Optimization

    .. automethod:: addAllocateFlowConstraint
    .. automethod:: addRouteAllConstraint
    .. automethod:: addLinkCapacityConstraint
    .. automethod:: addNodeCapacityConstraint
    .. automethod:: addNodeCapacityPerPathConstraint
    .. automethod:: addRequireAllNodesConstraint
    .. automethod:: addRequireSomeNodesConstraint
    .. automethod:: addRequireAllEdgesConstraint
    .. automethod:: addEnforceSinglePath
    .. automethod:: addBudgetConstraint
    .. automethod:: addMinDiffConstraint    
    .. automethod:: setPredefinedObjective
    .. autoattribute:: definedObjectives


Low-level API
-------------

These low-level functions are exposed to you, but you are discouraged from using them. 
Only use them for very fine-grained control over your optimization problem.

.. py:currentmodule:: sol.optimization.formulation.optbase

.. autoclass:: Optimization

    .. automethod:: xp
    .. automethod:: al
    .. automethod:: bn
    .. automethod:: be
    .. automethod:: bp

Solver-specific API
-------------------

If you know your optimization backend, here are some solver specific convenience methods.

CPLEX
~~~~~

.. py:currentmodule:: sol.optimization.formulation.cplexwrapper

.. autoclass:: OptimizationCPLEX
    
    .. automethod:: getCPLEXObject
    .. automethod:: getVarIndex
    .. automethod:: setName
    .. automethod:: setSolveTimeLimit
    .. automethod:: write
    .. automethod:: writeSolution


Helper Classes
--------------

Topology
~~~~~~~~
.. py:currentmodule:: sol.optimization.topology.topology
.. autoclass:: Topology
    :members:

Paths
~~~~~
.. py:currentmodule:: sol.optimization.topology.traffic
.. autoclass:: Path
    :members:

.. autoclass:: PathWithMbox
    :members:

Traffic
~~~~~~~
.. autoclass:: TrafficClass
    :members:

    .. automethod:: __init__

.. autoclass:: TrafficMatrix
    :members:

..
    SDN Propotype
    ~~~~~~~~~~~~~
    .. autoclass:: sol.sdn.controller.PanaceaController

Utils
~~~~~

.. automodule:: sol.utils.exceptions
    :members:

.. automodule:: sol.utils.pythonHelper
    :members:
    