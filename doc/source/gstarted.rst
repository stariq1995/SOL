Getting started with SOL
========================

Installing SOL
--------------

Dependencies
^^^^^^^^^^^^

SOL has multiple dependencies, most of which can be easily installed automatically using
`pip` (or similar package manager),
however `TMgen <https://github.com/progwriter/tmgen>`_ must be installed manually.
`Gurobi <http://www.gurobi.com/>`_ and the gurobipy package must be installed manually as well.

Download and install SOL
^^^^^^^^^^^^^^^^^^^^^^^^
The code is publicly available at `<https://github.com/progwriter/SOL>`_

1. Clone it using::

    git clone https://github.com/progwriter/SOL

2. (Optional, but **recommended**): setup a virtualenv (details `here <https://virtualenv.pypa.io/en/stable/>`_)

2. Install using development mode: ::

    pip install -e .

Understanding *Topology* and *Traffic Classes*
----------------------------------------------

Topology and Trafic Classes are basic inputs to the optimization; Before SOL
can crunch all the numbers, what we need in the *Topology* -- that is the network you are working with
and *Traffic Classes* -- the traffic that will be (or you think will be) flowing through the network.

Creating a basic optimization
-----------------------------

Once the Topology and Traffic Classes have been configured we can proceed to create a basic optimization.
Let's start with a very simple maxflow problem, a classic in the networking world.

To continue learning about SOL, and how to create more interesting problems, see the full `guide`
