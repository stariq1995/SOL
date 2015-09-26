## What is SOL?
SOL stands for <b>S</b>DN <b>O</b>ptimization <b>L</b>ayer and is a framework for developing networking applications.
Many modern SDN applications rely on creating optimizations in order to compute the optimal way to route traffic. SOL makes this much simpler by abstracting away

## How do I try it?
- Since code is still in development you have to clone the repo first:

    `git clone https://progwriter@bitbucket.org/progwriter/sol.git`

- Install dependencies.
    * First you need CPLEX. We cannot distribute it, but you can get a free academic license from IBM [here](http://www-01.ibm.com/support/docview.wss?uid=swg21419058)
    Install both the binaries and the python library.
    * Install python dependencies. *We strongly recommend the use of python [virtualenv](https://virtualenv.pypa.io/en/latest/)*

    `pip intall -r requirements.txt`
- Install SOL in *dev* mode:

    `pip install -e .`

- Tinker!
    * Look & run some examples from the *examples* folder
    * Write your own applications with the supplied [API]()

## How do I contribute?

Fork, code, submit pull request.
File issues.
You know the drill.
