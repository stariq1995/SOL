How to write SOL user-defined functions
=======================================

You can think of a user defined functions (UDFs) as a "callback functions" of sorts. They must follow a specific signature and will be called by SOL internally.

Note that :py:mod:`functools` module comes in very handy if your UDFs are complex or rely on additional parameters. More specifically :py:func:`functools.partial`


.. _predicate-howto:

Path Predicates
---------------
You provide a path predicate to the path-generation mechanism to test whether a path is valid.
Path predicate must follow this signature:

.. py:function:: predicate(path, topology)
    :noindex:

Let us look at some examples:

Every path is allowed: ::

    def allowAll(path, topology):
        return True

Allow only short paths: ::

    def allowShort(path, topology):
        return len(path) < 5

Only allow paths that go through node 4: ::

    def allowFour(path, topology):
        return (4 in path)

Something more complex:
Let's say you have a function that relies on some other parameters. ::
    
    def magicPredicate(path, topology, magicValue):
        if magicValue:
            return True  # Happy times!
        else:
            return False  # You shall not pass!

Then your predicate can be curried as follows: ::

    predicate = functools.partial(magicPredicate, magicValue=True)

Remember, you also get full power of :py:mod:`networkx` in this. So if you have some meta data stored in your topology, and you need it, use it!
Like so::

    def predicate(path, topology):
        G = topology.getGraph()
        # only allow paths that use all "good edges"
        good = True
        for u,v in path.getLinks():
            if not G.edge[u][v]['good_edge']:
                good = False
                break
        return good

Path modifier function
~~~~~~~~~~~~~~~~~~~~~~

This gives you the ability to manipulate a path object before running it through the predicate.
Currently we use this to expand a single path into multiple paths by choosing different combinations of middleboxes. 
For example::
    
    1 -> 2 -> 3 -> 4
    |    |    |    |
    m1   m2   m3   m4

gives 6 possible ways to choose 2 middleboxes. Thus the 
:py:func:`~sol.optimization.path.predicates.useMboxModifier` 
with expand one path object (1->2->3->4) into 6 
:py:class:`~sol.optimization.topology.traffic.PathWithMbox` 
objects. After this, you can determine using a predicate whether any of the 6 paths are valid.


Capacity functions
------------------

Capacity functions must compute the cost of processing a traffic class for a particular node/link and resource.
They must follow the following signature:

.. py:function:: capacityFunc(node_or_link, trafficClass, path, resource)
    :noindex:

Let us look at some simple examples:

A function that computes how expensive processing web traffic at a proxy is: ::

    def webTrafficProxyCost(node, trafficClass, path, resource):
        if trafficClass.name == 'web' and resource == 'mem':
            return trafficClass.volFlows * 10.0  # let's assume ten units of memory per flow
        else:
            raise ValueError("Wrong arguments")  # just in case something goes wrong

What if you wanted to normalize your load to be in the [0..1] range? ::
    
    def webTrafficProxyCost(node, trafficClass, path, resource, nodeCaps):
        if trafficClass.name == 'web' and resource == 'mem':
            return trafficClass.volFlows * 10.0 / nodeCaps[node]  # let's assume ten units of memory per flow
        else:
            raise ValueError("Wrong arguments")  # just in case something goes wrong
    # remember the currying from before:
    proxyCapacityFunc = functools.partial(webTrafficProxyCost, nodeCaps={1: 2000, 2: 50000, 3: 40000})

.. note::
    If you are normalizing your loads, then the capacities passed to the constraint function must be 1! Like so::

        opt.addNodeCapacityConstraint(pptc, 'cpu', {1: 1, 2: 1, 3: 1}, proxyCapacityFunc)

Lets explore some link capacity functions. Here is a really simple one: ::

    def defaultLinkFunc(link, tc, path, resource, linkCaps):
        # For simplicity assume only one type of traffic and one resource: bandwidth
        return tc.volBytes / linkCaps[link]  # Normalize bandwidth load to [0..1] range

What if you wanted to model link drops due to firewall or intrusion preventions rules? We can do it! ::

    def dropUpstreamLinkFunc(link, tc, path, resource, linkCaps, dropRates, cumulative=False):
        retention = 1 # fraction of retained traffic
        u, v = link
        droppedOnce = False  # have we processed/dropped on this path yet?
        for node in path:  # for each switch in path, assume switch doing the drops
            drop = dropRates.get(node, 0)  # consult our node drop fractions
            if drop > 0:
                droppedOnce = True
            if not droppedOnce or cumulative:  # if dropping cumulative or first in the chain
                retention -= drop
            if node == v:  # we have covered all the upstream nodes
                break
        return tc.trafficClass.avgSize * tc.volume * retention / linkCaps[link] # also normalize bandwidth usage

