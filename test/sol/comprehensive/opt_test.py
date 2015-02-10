from sol.optimization.formulation import getOptimization

__author__ = 'victor'

def opt_test():
    # TODO: remember to add other supported backends
    for backend in ['cplex']:
        opt = getOptimization(backend=backend)

        # todo: proceed constructing examples
