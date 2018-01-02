Common Questions
================

.. toctree::
  :maxdepth: 6

Do I have to use Gurobi? Why not optimizer *X*?
"""""""""""""""""""""""""""""""""""""""""""""""

Yes. It is an actively maintained, cross-platfom, well-performing
convex optimization solver. Additionally, academics can get a free license.
No plans to support other solvers soon.

I had a network with size *X* and the code is too slow.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""

This is likely for one of two reasons:

* You are unintentionally performing path generation (or selection) more than once. Path generation is a slow process,
  and results of path generation/selection should be saved for any subsequent optimizations.

* Your data is far too granular. If you are using a topology that includes hosts or have very
  fine-grained traffic classes, the problem size grows needlessly. Consider consolidating traffic classes and double check
  topology sizes.


Will you add feature X?
"""""""""""""""""""""""

Maybe. Depends on the feature, availability of the maintainers and the overall research direction
of the project. Feel free to open an issue on Github.

Is SOL thread-safe/concurrency-safe?
""""""""""""""""""""""""""""""""""""

No. No attempt has been made to make it thread-safe.

