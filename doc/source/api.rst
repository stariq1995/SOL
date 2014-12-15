SOL's APIs
==========

High-level API
--------------

.. py:currentmodule:: sol.optimization.formulation
.. autofunction:: getOptimization
.. autofunction:: generateFormulation

.. py:currentmodule:: sol.optimization.formulation.optbase
.. py:class:: Optimization

    .. automethod:: solve
    .. automethod:: getSolvedObjective
    .. automethod:: getPathFractions

Mid-level API
-------------

You can programatically "build" your optimization using the defined functions and constraints.

.. py:currentmodule:: sol.optimization.formulation.optbase

.. autoclass:: Optimization

    .. automethod:: addAllocateFlowConstraint
    .. automethod:: addRouteAllConstraint
    .. automethod:: addLinkCapacityConstraint
    .. automethod:: addNodeCapacityConstraint
    .. automethod:: addNodeCapacityIfActive
    .. automethod:: addRequireAllNodesConstraint
    .. automethod:: addRequireSomeNodesConstraint
    .. automethod:: addRequireAllEdgesConstraint
    .. automethod:: addEnforceSinglePath
    .. automethod:: addBudgetConstraint
    .. automethod:: addMinDiffConstraint

Objective manipulation


Low-level API
-------------

The functions are exposed to you, but you are discouraged from using them. Use them for very fine-grained control over your optimization problem.

.. py:currentmodule:: sol.optimization.formulation.optbase

.. autoclass:: Optimization

    .. automethod:: xp
    .. automethod:: al
    .. automethod:: bn
    .. automethod:: be
    .. automethod:: bp

Solver-specific APIs
--------------------

CPLEX
~~~~~

.. py:currentmodule:: sol.optimization.formulation.cplex

.. autoclass:: OptimizationCPLEX
    
    .. automethod:: getCPLEXObject
    .. automethod:: getVarIndex
    .. automethod:: setName


.. Gurobi
.. ~~~~~~

.. .. py:currentmodule:: sol.optimization.formulation.gurobi

.. .. autoclass:: OptimizationGurobi
..     :members:


Helper Classes
--------------

Topology
~~~~~~~~
.. py:currentmodule:: sol.optimization.topology.topology
.. autoclass:: Topology
    :members:

    .. automethod:: __init__

Paths
~~~~~
.. py:currentmodule:: sol.optimization.topology.traffic
.. autoclass:: Path
    :members:

    .. automethod:: __init__

.. autoclass:: PathWithMbox
    :members:

    .. automethod:: __init__

Traffic
~~~~~~~
.. autoclass:: TrafficClass
    :members:

    .. automethod:: __init__

.. autoclass:: TrafficMatrix
    :members:

SDN Propotype
~~~~~~~~~~~~~
.. autoclass:: sol.sdn.controller.PanaceaController