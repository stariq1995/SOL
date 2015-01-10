.. _examples:

Full Application Examples
=========================

Max Flow
---------------------

A very basic example that uses a high-level API kick start function and some easy Mid-level API functions.

.. literalinclude:: ../../examples/MaxFlow.py

SIMPLE
------

A little trickier. Requires you to have a good understanding of the optimization problem you're trying to solve
and the ability to write custom predicate and capacity functions.

Uses the mid-level API for a little more control over the optimization.

.. literalinclude:: ../../examples/SIMPLE.py

Elastic Tree
------------

An advanced example. Requires good understanding of optimization internals. Geared at researchers who are solving
novel networking optmization problems.

.. literalinclude:: ../../examples/ElasticTree.py