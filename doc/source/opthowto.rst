.. _opt-howto:

Determining your optimization model
===================================

This section gives you a quick into to SOL and helps you determine what you need to know about your problem before you start using SOL.

We assume you have a network and some sort of optimization problem you are solving. Thus you need:

* Network data
    * Your topology (switches, links, and any middleboxes that might be attached to the switches)
    * Traffic patterns in the network (between each ingress-egress, and types/volumes of traffic)
    * Node and link capacities (For different types of boxes)
* Problem Formulation
    * The objective function (maximize traffic flow, minimize load, etc.)
    * The list of constraints on network machines (Are boxes computationally constrained? Do you want to route all traffic, or best effort?)
    * Requirements on network paths (if any). Do you do waypoint enforcement? (e.g., proxy or firewall enforcement)

Types of constraints
--------------------

* Resource capacity (most common):
    CPU, Memory on middleboxes; TCAM on switches; Bandwidth on links; etc.
* Topology modification:
    Used if your problem allows toggling nodes or links on and off
* Other:
    Budget constraints, single path constraint, and other custom defined constraints.

A note on the data format
-------------------------

Naturally, for things to work smoothly, we need your data in a pre-determined format. We have tried to make it as simple as we could,
either using very basic data types, such as Python lists and dictionaries, or giving you an option to convert from a widely used format.
For example, we load topology data from a GraphML file.

That said, here are some explanations and pointers to data classes we use.

* Topology data: wrapped in :py:class:`~sol.optimization.topology.topology.Topology`, underneath it is a :py:module:networkx directed graph.
    You can directly create topologies from a GraphML file that stores graph of switches and links between them.
    
* Traffic classes: see :py:class:`~sol.optimization.topology.traffic.TrafficClass`
* Network paths: see :py:class:`~sol.optimization.topology.traffic.Path` and :py:class:`~sol.optimization.topology.traffic.PathWithMbox`
    for paths and paths with middleboxes in them.

Get me started!
---------------

Here we show you how to get started with a simple optimization. 
Say you would like to maximize the thoughput of traffic in your network.

#. Think of your constraints:
    #. Traffic must flow
    #. Do not overload links
#. Think of your objective:
    #. Maximize traffic flow
#. Think of your path requirements (if any):
    None, you're good to go

Gather your topology, and traffic data.
Now proceed to kikstart your optmization: ::

    opt, pptc = initOptimization(topology, trafficClasses, nullPredicate, 'shortest', 5)

* *nullPredicate* because any path will work for you. 
* 'shortest' and 5 are a way to reduce the number of paths in your optimization and speed it up

You get back two objects: *opt*, which is your optimization object and *pptc* which is paths per traffic class. You will use them as follows:

Add your constraints: ::

    # Traffic must flow!
    opt.allocateFlow(pptc)
    # Traffic must not overload links!
    opt.capLinks(pptc, 'bandwidth', linkCaps, defaultLinkCapFuncNoNorm)
    # Push as much traffic as we can!
    opt.setPredefObjective('maxminflow')

Solve the optimization ::

    opt.solve()

Get your solution::

    print opt.getSolvedObjective()  # let's see how much traffic we managed to push
    print opt.getPathFractions(pptc)  # this tells you how much traffic goes on each path

You're done!

See the :ref:`examples` section for the full version (and more applications with comments).

