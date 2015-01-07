Path generation
===============

This section describes currently available ways to generate network paths using the SOL framework.

"I don't care about paths"
--------------------------

If your problem really isn't path-oriented and any path will do, the solution is to use the 
:py:func:`~sol.optimization.path.predicates.nullPredicate`
when generating paths.
You can either generate paths beforehand (see below for lower-level function calls and examples), or specify 
:py:func:`~sol.optimization.path.predicates.nullPredicate`
in the config when you kick start your optimization, in which case SOL will do the generation for you.

.. note::
    Current release of SOL does not provide convenient parallelization for path generation when using high-level config.
    This is OK for small problems, but for larger problems, we recommend the use of the other API for path generation (see below) and 
    writing of your own parallelization routines. This will be fixed in future releases.

"I care about paths"
--------------------

There is currently one way to generate the paths, more may be implemented in the future.
This function generates all simple paths between two given nodes, and checks them against the given predicate.
Paths that pass the predicate are returned. To learn how to write your own custom predicates,
please see :ref:`predicate-howto`

.. autofunction:: sol.optimization.path.generate.generatePathsPerIE

A convenience method is also provided, if you want the use the same predicate across all traffic classes.
Beware, if multiple traffic classes use the same ingress and egress, paths will be re-computed for each traffic class,
which might not be very efficient.

Also, see the parallelization note above.

.. autofunction:: sol.optimization.path.generate.generatePathsPerTrafficClass