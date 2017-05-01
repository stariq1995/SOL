.. _guide-paths:

Paths
=====

Lets discuss how path generation and selection affects the outcomes of the optimization. Paths
are an important component to understaning how to enforce network policies and optmization
decision making.

Path generation
---------------

First and foremost we must generate paths that connect our ingress point to our egress points.


Handling Middleboxes
^^^^^^^^^^^^^^^^^^^^


All of the generated paths are then passed through a path predicate, to determine if the path is valid.
*This is how policies are enforced.*

Path predicates
^^^^^^^^^^^^^^^

A predicate is a function that decides whether a path is allowed or not.
SOL provides some built-in predicates, but it is very easy to write your own. A function with the following
signature is a valid predicate:

.. code-block:: python

    def predicate(path, topology)
        return True # or False


In fact, that is the implementation of the :py:func:`sol.path.predicates.null_predicate`, a predicate that
considers every path to be valid.

Predicates can perform arbitrary checks from ranging from useful to silly:
.. code-block:: python

    # Only consider a path valid if it has at least one middlebox
    def has_middlebox_predicate(path, topology):
        return any([topology.has_mbox(n) for n in path.nodes()])


    # Only consider a path valid if it has an IDS
    def has_ids_predicate(path, topology):
        return any(['ids' in topology.get_servies(n) for n in path.nodes()])

    # Flip a coin to decide if a path is valid
    def coin_flip_predicate(path, topology):
        return random.random > 0.5

    # Only allow paths where the number of links (hops) is even
    def only_even_hops_predicate(path, topology):
        return len(path.links()) % 2 == 0



Path selection
--------------

.. Robust path selection
   ^^^^^^^^^^^^^^^^^^^^^
