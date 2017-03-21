SOL: SDN Optimization Layer
===========================

SOL is a library that lets you rapidly prototype *network management applications* that
require constructing an **optimization**.
It is designed to work well with Software Defined Networking (SDN) as it makes use
of the global view of the network to compute a globally optimal (or near-optimal)
solution.

Why optimizations?
------------------

Optimization is incredibly common in the networking domain.
Classic problems such as shortest path routing and maxflow can all be expressed as
`linear programs <https://en.wikipedia.org/wiki/Linear_programming>`_
and solved efficiently.

Traffic engineering, middebox management, and other types of load balancing
can also be expressed using optimizations.

Key features
------------

* Fast prototyping of optimizations for network management
* Composition of multiple optimization applications using different fairness modes
* Flexible resource computation logic
* Integrations with `ONOS <http://onosproject.org/>`_ SDN controller
* Novel optimization capabilities, reusable across different applications,\
  (e.g., reconfiguration minimization)


Integrations
------------

SOL is desgined to be modular and could potentially integrate with multiple
SDN controllers. This library contains the core optimization logic. It can be used
on its own to quickly prototype applications, compose_apps multiple optimizations
and examine resulting solutions.

A rough view of the SOL library and integrations is as follows:


* `SOL library <https://github.com/progwriter/SOL>`_ (this project/repository)
* `ONOS integration <https://github.com/progwriter/sol-onos>`_ Allows use of the SOL library from the\
  `ONOS <http://onosproject.org/>`_  controller
* `SOL workflows <https://github.com/progwriter/SOL-workflows>`_ A collection of examples and workflows to
  give users an idea of how SOL can be used.
* `TMgen library <https://github.com/progwriter/tmgen>`_ A helper library for generating and manipulating
  traffic matrices.


Python documentation
--------------------

.. Available at `Read the Docs <http://sol.readthedocs.io/>`_ (unless you're already here).

.. toctree::
   :maxdepth: 2

   gstarted.rst
   guide.rst
   api.rst
   faq.rst
   dev.rst
