Getting started with SOL
========================

Installing SOL
--------------

Supported python versions
^^^^^^^^^^^^^^^^^^^^^^^^^

Both python 2.7 and 3.4 and above are supported, although most testing was performed with python version 3.5 only.

Dependencies
^^^^^^^^^^^^

SOL has multiple dependencies, most of which can be easily installed automatically using
`pip` (or `conda` or similar package manager)::

    pip install -r requirements.txt

however `TMgen <https://github.com/progwriter/tmgen>`_ and
`Gurobi <http://www.gurobi.com/>`_ must be **installed manually**.

While Gurobi is a commercial product, free academic licensing is
`available <http://www.gurobi.com/products/licensing-pricing/licensing-overview>`_

**Optional but recommended**

  1. `Anaconda <https://www.continuum.io/downloads>`_ by Continuum.io
  It has many of the required scientific python packages and even an easily installable gurobi Python package.

  2. We also recommend setting up a virtualenv (either using `conda` or `virtualenv <https://virtualenv.pypa.io/en/stable/>`_)
  for convenience.


Download and install SOL
^^^^^^^^^^^^^^^^^^^^^^^^
The code is publicly available at `<https://github.com/progwriter/SOL>`_

1. Clone it using::

    git clone https://github.com/progwriter/SOL

2. Install SOL development mode: ::

    pip install -e .

Understanding fundamental inputs to SOL
---------------------------------------

SOL requires the following things to correctly do its job:

* Network topology
* Information about network traffic
* The application's optimization goals and constraints

In this quickstart guide we describe the necessary inputs and show how to create a simple application.
We will go over how to construct a very small network and create a simple
`maxflow <https://en.wikipedia.org/wiki/Maximum_flow_problem>`_ optimization.

Topology
^^^^^^^^

The :py:class:`sol.Topology` class represents the network as a graph.

Each node (vertex) in the graph denotes a switch/router and is identified by an integer ID.
The topology also stores data about network functions and resources.
That is, each node will have attributes indicating whether it has a middlebox attached to it,
what functions it performs (e.g., 'firewall') and any resources/capacities associated with this node.

Each edge, naturally, represents a link between any two given nodes (a tuple of ints) and is also allowed to
have resources/capacities asscociated with it.

Lets look at some examples. SOL includes some primitive topology generators:

>>> from sol.topology.generators import chain_topology
>>> t = chain_topology(5)
>>> list(t.nodes()) # topology nodes
[0, 1, 2, 3, 4]

Lets add a middlebox to node 3, and make it a firewall:

>>> t.set_mbox(3)
>>> t.add_service_type(3, 'firewall')
>>> t.set_resource(3, 'cpu', 3000)
>>> list(t.nodes(data=True))
[(0, {'resources': {}, 'services': 'switch'}),
 (1, {'resources': {}, 'services': 'switch'}),
 (2, {'resources': {}, 'services': 'switch'}),
 (3,
  {'hasMbox': 'True',
   'resources': {'cpu': 3000.0},
   'services': 'firewall;switch'}),
 (4, {'resources': {}, 'services': 'switch'})]

Topologies can also be created by loading existing data from disk. GraphML and GML formats
are supported. Note that to store resources GML format should be used, as it supports
nested attributes for nodes and edges.

>>> from sol import Topology
>>> t.write_graph('mytopo.gml')
>>> t2 = Topology('mynewtopo')
>>> t2.load_graph('mytopo.gml')
>>> list(t2.nodes(data=True)) # all the data is preserved
[(0, {'resources': {}, 'services': 'switch'}),
 (1, {'resources': {}, 'services': 'switch'}),
 (2, {'resources': {}, 'services': 'switch'}),
 (3,
  {'hasMbox': 'True',
   'resources': {'cpu': 3000.0},
   'services': 'firewall;switch'}),
 (4, {'resources': {}, 'services': 'switch'})]

See full topology API in :ref:`topoapi` section.
For now, let us simply define link capacities in the network to be a 100 units (imagine it's Mb/s)

>>> for link in t.links():
>>>     t.set_resource(link, 'bandwidth', 100)


Traffic Classes
^^^^^^^^^^^^^^^

Traffic classes contain information about the type of traffic being routed through the network.
The optimization later will determine how to best route this traffic, but to do so it needs to know entrance and exit
points for traffic and its volume.
Therefore, at a minimum,
each traffic class must contain a source node, a destination node and volume of traffic (i.e., number of flows).
For example:

>>> from sol import make_tc
>>> make_tc(0, 4, 1000) # a traffic class from node 0 to node 4 with 1000 flows
TrafficClass(tcid=0,name=,src=0,dst=4)


You can construct traffic classes directly, however you will need to keep track of traffic class ids
(they must be sequential) and provide volumes as numpy arrays:

>>> from sol import TrafficClass
>>> import numpy
>>> tc = TrafficClass(tcid=1, name='myclass', src=0, dst=4, vol_flows=numpy.array([1000]))

Detailed explanation for this is given in :ref:`guide-tc` section of the User's Guide.

Paths (per traffic class)
^^^^^^^^^^^^^^^^^^^^^^^^^

Each traffic class is assigned a set of valid paths.
Generating and filtering paths using *predicates* is how policies are enforced.
Usually, this is a one time, offline step. Any sufficiently complex application will
implement its own predicate generate paths and store them for future use. In this simple guide,
we will just generate paths on-the-fly using one of SOL's helper functions, since there
are no policy requirements on which paths the traffic must take in the maxflow problem.

>>> from sol.path.generate import generate_paths_tc
>>> pptc = generate_paths_tc(t, [tc]) # get our earlier topology and put the traffic class in a list
>>> pptc
<sol.path.paths.PPTC at 0x10dc00f98>

Let us treat *pptc* as an opaque object for now.
You will need it to construct the application;
We will detail the need for :py:class:`sol.PPTC` class
and its capabilities in the :ref:`guide-paths` section of the User's Guide.

Applications
^^^^^^^^^^^^

Once the paths per traffic class have been configured, we can proceed to create a basic optimization.
Let's start with a very simple maxflow problem.

.. code-block:: python

    from sol import AppBuilder
    from sol.opt.funcs import CostFuncFactory

    builder = AppBuilder()
    # Create a cost function where each flow consumes 1 Mb/s regardless of traffic class
    cost_func = CostFuncFactory.from_number(1)
    # cost_func
    # builder.build()
    app = builder.name('maxflowapp').pptc(pptc).objective('maxflow')\
        .add_resource('bandwidth', cost_func).build()

The application builder allows us to set the *pptc* of the application, use a pre-defined
maxflow objective function, as well as set the routing cost of traffic.
In this example, each flow consumes a unit of bandwidth. SOL provides a convenitent way
of specifying that using the :py:class:`sol.opt.funcs

Optimization
------------

With a single app
^^^^^^^^^^^^^^^^^

The optimization is constucted using the topology and the application:

>>> from sol import from_app
>>> opt = from_app(topology, app)
>>> opt.solve() # solve the optimization

With multiple apps
^^^^^^^^^^^^^^^^^^

See the :ref:`composition` part of the User's Guide.

Examining the solutions
-----------------------

The two main ways of examining the solution are:

1. Looking at the value of the objective function
2. Extracting the paths responsible for carrying traffic.

1. To see the objective function value, simply run:

>>> opt.get_solved_objective(app)
0.5

As expected, we can route 50% of the traffic, due to the link caps.

2. To extract the paths

  >>> p = opt.get_paths()
  >>> p
