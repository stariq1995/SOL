## What is SOL? [![Build Status](https://travis-ci.org/progwriter/SOL.svg?branch=master)](https://travis-ci.org/progwriter/SOL)
SOL stands for SDN Optimization Layer and is a framework for developing
networking applications. Many modern SDN applications rely on creating
optimizations in order to compute the optimal way to route traffic. SOL makes
this much simpler by abstracting away some of the low-level optimization details
and interfacing with SDN controllers on your behalf.

## How do I try it?
- Since code is still in development you have to clone the repo,
there is no option to use PyPi yet:

    `git clone https://bitbucket.org/progwriter/sol.git`

- Install dependencies.
    * First, you need CPLEX. We cannot distribute it, but you can get a free academic license from IBM [here](http://www-01.ibm.com/support/docview.wss?uid=swg21419058).
    Install *both the binaries and the python library*.
    * Install python dependencies. **We strongly recommend** the use of python
    [virtualenv](https://virtualenv.pypa.io/en/latest/)

    `pip install -r requirements.txt`
- Install SOL in *development* mode.

    `pip install -e .`
- Tinker!
    * Look at & run some examples from the *examples* folder
    * Write your own applications with the supplied API

## How do I contribute?

Fork, code, submit pull request.
File issues.
You know the drill.

