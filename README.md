SOL: SDN Optimization Layer
===========================

SOL is a library that lets you rapidly prototype *network management applications* that require constructing an **optimization**. 
It is designed to work well with Software Defined Networking (SDN) as it makes use of the global view of the network to 
compute a globally optimal (or near-optimal) solution.

This repository contains the implementation of both the SOL libary, 
and its extension **Chopin**, which allows intent-driven composition of multiple
SDN applications. 

Why optimizations?
------------------

Optimization is incredibly common in the networking domain. Classic problems such as shortest path routing and maxflow 
can all be expressed as [linear programs](https://en.wikipedia.org/wiki/Linear_programming) and solved efficiently.

Traffic engineering, middebox management, and other types of load balancing can also be expressed using optimizations.

Key features
------------

-   Fast prototyping of optimizations for network management
-   Composition of multiple optimization applications using different fairness modes
-   Flexible resource computation logic
-   Integrations with [ONOS](http://onosproject.org/) SDN controller
-   Novel optimization capabilities, reusable across different applications,
    (e.g., reconfiguration minimization)

Integrations
------------

SOL is desgined to be modular and could potentially integrate with multiple SDN controllers. 
This library contains the core optimization logic. It can be used on its own to quickly prototype applications, 
compose multiple optimizations and examine resulting solutions.

A rough view of the SOL library and integrations is as follows:

-   [SOL library](https://github.com/progwriter/SOL) (this repository)
-   [ONOS integration](https://github.com/progwriter/sol-onos) Allows use of the SOL library from the
    [ONOS](http://onosproject.org/) controller
-   [TMgen library](https://github.com/progwriter/tmgen) A helper library for generating and manipulating traffic matrices.

Disclaimer
----------
SOL is a research project under development. Some APIs, integrations and documentation/links are subject to
change.

Original papers
---------------

* [SOL](http://cs.unc.edu/~victor/papers/sol.pdf)
* Chopin (to appear in CoNEXT'2018)


Python documentation
--------------------

Available at [Read the Docs].

[Read the Docs]: http://sol.readthedocs.io/
