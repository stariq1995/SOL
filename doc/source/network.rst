Network Topology
================

Network topologies are represented as directed graphs using the `networkx <https://networkx.github.io/>`_ library.
In addition to


.. _guide-tc:

Traffic Classes
===============

To create a traffic class, you have two options: directly calling the traffic class constuctor
or relying on the :py:func:`sol.make_tc` function, which is syntactic sugar with internal state keeping track
of traffic class ID numbers.

If using *make_tc*, specify only source and destination nodes, and volume in flows.

>>> from sol import make_tc
>>> make_tc(0, 4, 20) # a traffic class from node 0 to node 4 with 20 flows


If using the contructor, specify the ID (must be unique and sequential), name, src/dst nodes and volumes.


.. warning::
    Do not mix the two methods of traffic class creation, as :py:func:`sol.make_tc` function
    maintains an internal traffic class ID counter, which will become out of sync if