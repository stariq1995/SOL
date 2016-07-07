Getting started with SOL
========================

Installing SOL
--------------

Dependencies
^^^^^^^^^^^^

SOL has multiple dependencies, most of which can be easily installed automatically using
`pip` (or similar package manager),
however `TMgen <https://github.com/progwriter/tmgen>`_ must be installed manually.
`Gurobi <http://www.gurobi.com/>`_ and the python interface must be installed as well.

Download and install SOL
^^^^^^^^^^^^^^^^^^^^^^^^
The code is publicly available at `<https://github.com/progwriter/SOL>`_

1. Clone it using::

    git clone https://github.com/progwriter/SOL

2. (Optional, but **recommended**): setup a virtualenv (details `here <https://virtualenv.pypa.io/en/stable/>`_)

2. Install using development mode: ::

    pip install -e .

Creating an optimization
------------------------
