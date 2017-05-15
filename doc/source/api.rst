SOL API
=======

This describes APIs for manipulating different types of objects that SOL
implements and uses, such as :py:class:`sol.Topology`,
:py:class:`sol.TrafficClass`, etc.


.. toctree::
  :maxdepth: 1

.. py:currentmodule:: sol

.. _topoapi:

Topology
--------

.. autoclass:: Topology
    :special-members: __init__
    :members:

TrafficClass
------------


.. autoclass:: TrafficClass
    :special-members: __init__
    :members:



Application
-----------

.. py:currentmodule:: sol
.. autoclass:: App
    :special-members: __init__
    :members:

.. autoclass:: AppBuilder
    :special-members: __init__
    :members:


Path objects
------------

.. autoclass:: sol.Path
    :members:

.. autoclass:: sol.PathWithMbox
    :members:

.. autoclass:: sol.PPTC
    :members:


Path generation and selection
-----------------------------

.. automodule:: sol.path.generate
    :members:

.. automodule:: sol.path.predicates
    :members:

.. automodule:: sol.path.select
    :members:
    :exclude-members: rand, choice


Optimization
------------

.. automodule:: sol.opt.quickstart
    :members:

.. py:currentmodule:: sol.opt.gurobiwrapper
.. autoclass:: OptimizationGurobi
    :members:


Utils & Logging
---------------

.. automodule:: sol.utils.ph
    :members:

.. automodule:: sol.utils.logger
    :members:

Topology generators
-------------------

.. automodule:: sol.topology.generators
    :members:

Topology Provisioning
---------------------

.. automodule:: sol.topology.provisioning
    :members:
    :undoc-members:

Exceptions
----------

.. automodule:: sol.utils.exceptions
    :members:
