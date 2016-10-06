SOL API
=======

This describes APIs for manipulating different types of objects that SOL
implements and uses, such as :py:class:`sol.topology.topologynx.Topology`,
:py:class:`sol.topology.traffic.TrafficClass`, etc.

Topology
--------

.. py:currentmodule:: sol.topology.topologynx
.. autoclass:: Topology
    :special-members: __init__
    :members:

TrafficClass
------------

.. py:currentmodule:: sol.topology.traffic
.. autoclass:: TrafficClass
    :special-members: __init__
    :members:

:attribute: ID
  Positive integer that uniquely identifies the traffic class

:attribute: name
  String name of this traffic class. Multiple traffic classes may share a
  name for convenience (e.g., 'web', 'ssh')



Application
-----------

.. py:currentmodule:: sol.opt.app
.. autoclass:: App
    :special-members: __init__
    :members:


Path generation and selection
-----------------------------

.. automodule:: sol.path.generate
    :members:

.. automodule:: sol.path.select
    :members:


Optimization
------------

.. automodule:: sol.opt.quickstart

.. py:currentmodule:: sol.opt.gurobiwrapper
.. autoclass:: OptimizationGurobi
    :members:
