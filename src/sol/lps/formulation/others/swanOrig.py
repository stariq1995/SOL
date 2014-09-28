""" SWAN formulation from the paper """
from __future__ import division

try:
    # noinspection PyUnresolvedReferences
    import cplex
except ImportError as e:
    print 'Need IBM CPLEX API, ' \
          'make sure it is installed and in your pythonpath'
    raise e
import itertools
import math


def SWANAllocation(topology, **kwargs):
    """
    Run the SWAN optimization described in the paper
    :param topology: topology to run this on
    :param kwargs:
    :return: flow fractions per commodity
    """
    G = topology.getGraph()
    linkcaps = {(u, v): G.edge[u][v]['capacity'] for u, v in G.edges_iter()
                if 'capacity' in G.edge[u][v]}
    fullcaps = linkcaps.copy()
    classes = kwargs.get('classes')
    commodities = kwargs.get('paths')
    alpha = kwargs.get('alpha')
    U = kwargs.get('U')
    scratch = kwargs.get('scratch')
    objective = kwargs.get('objective', 'throughput')
    result = {}
    for cl in classes:
        classComms = {k: v for k, v in commodities.iteritems() if
                      k.trafficClass == cl}
        if objective == 'fairness':
            flow = _approxMMF(cl, linkcaps, alpha, U, classComms,
                              fullcaps, scratch)
        elif objective == 'throughput':
            flow = _throuphutMAX(cl, linkcaps, classComms, fullcaps, scratch)
        else:
            raise ValueError('Unknown objective for SWAN')
        for link in linkcaps:
            s = 0
            for k in flow:
                for j, path in enumerate(classComms[k]):
                    if link in itertools.izip(path, path[1:]):
                        s += flow[k][j]
            linkcaps[link] -= s
        result.update(flow)
    # for k in result:
    #     for j in flow[k]:
    #         flow[k][j] /= k.volume
    return result


def _approxMMF(cl, linkcaps, alpha, U, comms, fullcaps, scratch):
    """

    :param cl: the traffic class
    :param linkcaps: residual link capacities
    :param alpha:
    :param U:
    :param comms:
    :param fullcaps:
    :param scratch:
    :return:
    """
    T = int(math.ceil(math.log(max([k.volume for k in comms]) / U, alpha)))
    flow = {}
    communsat = comms.copy()
    commsat = {}
    print cl.name,
    for iteration in xrange(1, T):
        res = _swanMCF(cl, linkcaps, (alpha ** (iteration - 1)) * U,
                       (alpha ** iteration) * U, commsat, communsat, flow,
                       fullcaps, scratch)
        for k in res:
            bi = sum(res[k])
            # if k.ID == 36:
            # print bi, k.volume, (alpha ** iteration)*U
            if k not in flow and (bi < min(k.volume, (alpha ** iteration) * U)
                                  or bi == k.volume):
                flow[k] = res[k]
                commsat[k] = comms[k]
                del communsat[k]
    # print ''
    return flow


def _throuphutMAX(cl, linkcaps, comms, fullcaps, scratch):
    return _swanMCF(cl, linkcaps, 0, float('inf'), {}, comms, {}, fullcaps,
                    scratch)


def _swanMCF(cl, linkcaps, blow, bhigh, commsat, communsat, flow, fullcaps,
             scratch):
    """
    :param cl: the traffic class
    :param linkcaps:
    :param blow:
    :param bhigh:
    :param commsat:
    :param communsat:
    :param flow:
    :param fullcaps:
    :param scratch:
    :return:
    """
    comms = commsat.copy()
    comms.update(communsat)

    prob = cplex.Cplex()
    # add variables
    prob.variables.add(names=['b_{}_{}'.format(k.ID, j) for k in comms
                              for j in xrange(len(comms[k]))],
                       lb=[0] * len([x for k in comms for x in comms[k]]),
                       ub=[k.volume for k in comms for x in comms[k]])
    prob.variables.add(names=['b_{}'.format(k.ID) for k in communsat],
                       lb=[blow] * len(communsat),
                       ub=[min(bhigh, k.volume) for k in communsat])
    # for k in communsat:
    #     print bhigh, k.volume
    prob.variables.add(names=['b_{}'.format(k.ID) for k in commsat])
    prob.variables.add(names=['obj'], lb=[0])
    v = prob.variables.get_names()
    varindex = dict(itertools.izip(v, range(len(v))))

    # b_i = sum(b_ij)
    for k in comms:
        var = [varindex['b_{}_{}'.format(k.ID, j)]
               for j in xrange(len(comms[k]))]
        mults = [1] * len(var)
        var.append(varindex['b_{}'.format(k.ID)])
        mults.append(-1)
        prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                    rhs=[0], senses='E',
                                    names=['commsum.{}'.format(k.ID)])

    # b_i = f_i, except b_ij = f_ij
    for k in commsat:
        l = len(commsat[k])
        ind = range(l)
        prob.linear_constraints.add(
            [cplex.SparsePair([varindex['b_{}_{}'.format(k.ID, j)]], [1])
             for j in ind],
            rhs=[flow[k][j] for j in ind],
            senses='E' * l)

    # link capacity constraints
    # print comms
    for l in linkcaps:
        mults = {}
        rhs = min(linkcaps[l], (1 - scratch[cl.name]) * fullcaps[l])
        for k in comms:
            for pi, path in enumerate(comms[k]):
                if l in itertools.izip(path, path[1:]):
                    mults[varindex['b_{}_{}'.format(k.ID, pi)]] = cl.avgSize
        if mults:
            ind, mult = zip(*mults.iteritems())
            prob.linear_constraints.add([cplex.SparsePair(ind, mult)],
                                        rhs=[rhs], senses=['L'],
                                        names=['linkcap.{}_{}'.format(l[0],
                                                                      l[1])])

    # objective here
    var = [varindex['b_{}'.format(k.ID)] for k in comms]
    mults = [1] * len(var)
    # var.extend([varindex['b_{}_{}'.format(k.ID, j)] for k in comms
    # for j in xrange(len(comms[k]))])
    #mults.extend([-1e-02 * len(x) for k in comms for x in comms[k]])
    var.append(varindex['obj'])
    mults.append(-1)
    prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                rhs=[0], senses='E', names=['objfunc'])
    prob.objective.set_sense(prob.objective.sense.maximize)
    prob.objective.set_linear('obj', 1.0)

    prob.write('swan.lp')
    # prob.set_log_stream(None)
    # prob.set_results_stream(None)
    prob.solve()
    if not prob.solution.get_status() == 1:
        print 'status', prob.solution.get_status()
        raise Exception('no optimal solution')
    return {k: [prob.solution.get_values('b_{}_{}'.format(k.ID, i))
                for i in xrange(len(comms[k]))]
            for k in comms}
