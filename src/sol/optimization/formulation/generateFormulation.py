""" Generates the formulation for Panacea"""

from __future__ import division
import itertools

from panacea.lps.formulation import funcs
from panacea.util.exceptions import InvalidConfigException, \
    UnsupportedOperationException, NoPathsException
from panacea.util.pythonHelper import tup2str, Tree
from panacea.lps.topology.traffic import PathWithMbox


try:
    # noinspection PyUnresolvedReferences
    import cplex
except ImportError as ex:
    print 'Need IBM CPLEX API, ' \
          'make sure it is installed and in your pythonpath'
    raise ex
from itertools import izip
from collections import defaultdict


def _pv(commodity, pathIndex):
    """ Convenience method for creating a decision variable

    :param commodity: the commodity objects, needed for the ID
    :param pathIndex: index of the path
    :returns: variable name of the form *x_commid_pathind*
    :rtype: string
    """
    return 'x_{}_{}'.format(commodity.ID, pathIndex)


def startProblem():
    """ Create a new instance of the cplex problem

    :return: :py:class:`~cplex.Cplex` instance
    """
    prob = cplex.Cplex()
    return prob


def defineVar(prob, name, coeffs, const=0):
    """ Utility function to define an (almost) arbitrary variable.

    :param prob: cplex instance problem
    :param name: name of the variable
    :param coeffs: coefficients of other variables that define this variable, a
        dictionary of strings to floats.
        If None, then only the names is defined, with no value or no bounds
        assigned to it.
    :param const: any non-coefficient slack
    """
    prob.variables.add(names=[name])
    if coeffs is None:
        return
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    var = coeffs.keys()
    mults = coeffs.values()
    var.append(varindex[name])
    mults.append(-1.0)
    prob.linear_constraints.add([cplex.SparsePair(ind=var, val=mults)],
                                senses=['E'], rhs=[const])


def setObjective(prob, coeffs, sense):
    """
    :param prob: cplex problem instance
    :param coeffs: dictionary mapping variables to coefficients
    :param sense: *min* or *max* indicates whether we are minimizing or
        maximizing the objective
    """
    if sense.lower() not in ['max', 'min', 'maximize', 'minimize']:
        raise InvalidConfigException('Unknown optimization task')
    s = prob.objective.sense.minimize
    if sense.lower() == 'max' or sense.lower() == 'maximize':
        s = prob.objective.sense.maximize
    prob.objective.set_sense(s)
    prob.objective.set_linear(coeffs.items())


def addDecisionVariables(prob, ppk):
    """ Add and set bounds on the flow fraction variables
    :param prob: cplex problem instance
    :param ppk: paths per commodity
    """
    var = []
    for k in ppk:
        for pi in xrange(len(ppk[k])):
            var.append(_pv(k, pi))
    prob.variables.add(names=var, lb=[0] * len(var), ub=[1] * len(var))


def addBinaryVariables(prob, ppk, topology, types=None):
    """

    :param prob:
    :param ppk:
    :param topology:
    :param types:
    :return:
    """
    graph = topology.getGraph()
    # if types is None:
    # types = ['node', 'edge', 'path']
    if 'node' in types:
        var = ['binnode_{}'.format(n) for n in graph.nodes_iter()]
        prob.variables.add(names=var,
                           types=[prob.variables.type.binary] * len(var),
                           lb=[0] * len(var),
                           ub=[1] * len(var))
    if 'edge' in types:
        var = ['binedge_{}_{}'.format(u, v) for u, v
               in graph.edges_iter()]
        prob.variables.add(names=var,
                           types=[prob.variables.type.binary] * len(var),
                           lb=[0] * len(var),
                           ub=[1] * len(var))
    if 'path' in types:
        var = ['binpath_{}_{}'.format(k.ID, pi) for k in ppk
               for pi in xrange(len(ppk[k]))]
        prob.variables.add(names=var,
                           types=[prob.variables.type.binary] * len(var),
                           lb=[0] * len(var),
                           ub=[1] * len(var))


def addRoutingCost(prob, ppk):
    """ Defines the routing cost constraint

    :param prob: the cplex problem instance
    :param ppk: paths per commodity
    """
    coeffs = {}
    for k in ppk:
        for pi, path in enumerate(ppk[k]):
            coeffs[_pv(k, pi)] = len(path)-1
    defineVar(prob, 'RoutingCost', coeffs)


def addRouteAllConstraints(prob, ppk):
    """ Adds coverage constraints (aka flow conservation)

    :param prob: the cplex problem instance
    :param ppk: paths per commodity
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for k in ppk:
        var = []
        for pi in range(len(ppk[k])):
            var.append(varindex[_pv(k, pi)])
        mults = [1] * len(var)
        prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                    senses=['E'], rhs=[1],
                                    names=['Coverage.k.{}'.format(k.ID)])


def addAllocateFlowConstraints(prob, ppk, comms=None, allocationval=None,
                               setEqual=False):
    """ Adds demand constraints for given commodities

    :param setEqual:
    :param prob: cplex problem instance
    :param ppk: paths per commodity
    :param comms: commodities for which the demand constraints should be added
    :param allocationval: exisiting allocation values for the commodities
        If none, appropriate decision variables will be created
    """
    v = prob.variables.get_names()
    for k in comms:
        if 'allocation' not in v:
            prob.variables.add(names=['allocation_{}'.format(k.ID)],
                               lb=[0], ub=[k.volume])
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    if comms is None:
        comms = ppk.iterkeys()
    for k in comms:
        var = []
        mults = []
        for pi in range(len(ppk[k])):
            var.append(varindex[_pv(k, pi)])
            mults.append(k.volume)
        prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                    senses=['L'], rhs=[k.volume],
                                    names=['DemandCap.k.{}'.format(k.ID)])
        mults = [x / k.weight for x in mults]
        if allocationval is None:
            var.append(varindex['allocation_{}'.format(k.ID)])
            mults.append(-1)
            rhs = [0]
        else:
            rhs = [-allocationval]
        prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                    senses='G', rhs=rhs,
                                    names=['Demand.k.{}'.format(k.ID)])
    if setEqual:
        for k1, k2 in itertools.izip(comms, comms[1:]):
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex['allocation_{}'.format(k1.ID)],
                                   varindex['allocation_{}'.format(k2.ID)]],
                                  [1, -1])],
                rhs=[0], senses='E')


# TODO: add customFUNC
def addNodeCapacityConstraints(prob, ppk, nodecaps, maxload=False):
    """ Add node constraints

    :param prob: cplex problem instance
    :param ppk: paths per commodity
    :param nodecaps: multi-dict containing a mapping of nodes to resources to\
        capacities. For exapmle::
            nodecaps[1]['cpu'] = 10

        means that cpu capacity of node 1 is 10 units

    :param maxload:
    """
    if 'LoadFunction' not in prob.variables.get_names():
        prob.variables.add(names=['LoadFunction'])

    for node in nodecaps:
        for resource in nodecaps[node]:
            loadstr = '{}Load_{}'.format(resource, node)
            prob.variables.add(names=[loadstr])

    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for node in nodecaps:
        for resource in nodecaps[node]:
            cap = nodecaps[node][resource]
            loadstr = '{}Load_{}'.format(resource, node)
            var = [varindex[loadstr]]
            mults = [-1]
            # nodes with capacities
            for k in ppk:
                cl = k.trafficClass
                for pi, path in enumerate(ppk[k]):
                    if isinstance(path, PathWithMbox) and path.usesBox(node):
                        # or (node in path):
                        multiplier = cl[resource + 'cost'] * k.volume / cap
                        mults.append(multiplier)
                        var.append(varindex[_pv(k, pi)])
            prob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults),
                 cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                senses=['E', 'L'], rhs=[0, 1.0],
                names=['{}Load.{}'.format(resource, node),
                       '{}Cap.{}'.format(resource, node)])
            if maxload:
                prob.linear_constraints.add(
                    [cplex.SparsePair(ind=[varindex['LoadFunction'],
                                           varindex[loadstr]],
                                      val=[1.0, -1.0])],
                    senses=['G'], rhs=[0],
                    names=['MaxLoad.{}'.format(node)])


def addLinkConstraints(prob, ppk, linkcaps, maxlink=False, customFunc=None):
    """ Write out link constraints for each link in the network

    :param customFunc:
    :param prob: cplex problem instance
    :param ppk: paths per commodity
    :param linkcaps: dictionary mapping links to capacities
    :param maxlink: if True, add constraints for tracking maximum link load
    """
    if maxlink and 'LinkLoadFunction' not in prob.variables.get_names():
        prob.variables.add(names=['LinkLoadFunction'])

    # add our variables first
    for link in linkcaps:
        u, v = link
        cap = linkcaps[link]
        if cap > 0:
            linkstr = tup2str((u, v))
            loadstr = 'LinkLoad_{}'.format(linkstr)
            prob.variables.add(names=[loadstr])

    vn = prob.variables.get_names()
    varindex = dict(izip(vn, range(len(vn))))
    if customFunc is None:
        customFunc = funcs.curryLinkConstraintFunc(funcs.defaultLinkFunc,
                                                   linkcaps=linkcaps)
    for link in linkcaps:
        cap = linkcaps[link]
        u, v = link
        if cap > 0:
            linkstr = tup2str((u, v))
            loadstr = 'LinkLoad_{}'.format(linkstr)
            var = [varindex[loadstr]]
            mults = [-1]
            for k in ppk:
                for pi, path in enumerate(ppk[k]):
                    if link in izip(path, path[1:]):
                        multiplier = customFunc(k, path, link)
                        mults.append(multiplier)
                        var.append(varindex[_pv(k, pi)])
            prob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults),
                 cplex.SparsePair(ind=[varindex[loadstr]], val=[1.0])],
                senses=['E', 'L'], rhs=[0, 1],
                names=['LinkLoad.{}'.format(linkstr),
                       'LinkCap.{}'.format(linkstr)])
            if maxlink:
                prob.linear_constraints.add(
                    [cplex.SparsePair([varindex['LinkLoadFunction'],
                                       varindex[loadstr]],
                                      [1.0, -1.0])],
                    senses=['G'], rhs=[0],
                    names=['MaxLinkLoad.{}'.format(linkstr)])


# TODO: add customFUNC
def addDiscreteLoadConstraints(prob, ppk, nodecaps, maxload=False):
    """
    :param prob:
    :param ppk:
    :param nodecaps:
    :return:
    """
    for node in nodecaps:
        for resource in nodecaps[node]:
            loadstr = '{}DLoad_{}'.format(resource, node)
            prob.variables.add(names=[loadstr])
    if 'DLoadFunction' not in prob.variables.get_names():
        prob.variables.add(names=['DLoadFunction'])

    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for node in nodecaps:
        for resource in nodecaps[node]:
            cap = nodecaps[node][resource]
            loadstr = '{}DLoad_{}'.format(resource, node)
            var = [varindex[loadstr]]
            mults = [-1]
            for k in ppk:
                for pi, path in enumerate(ppk[k]):
                    if node in path:
                        var.append(varindex['binpath_{}_{}'.format(k.ID, pi)])
                        mults.append(1)
            prob.linear_constraints.add(
                [cplex.SparsePair(ind=var, val=mults)],
                rhs=[0], senses=['E'],
                names=['{}DLoad.{}'.format(resource, node)])
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex[loadstr]], [1])],
                rhs=[cap], senses=['L'],
                names=['{}Cap.{}'.format(resource, node)])
            if maxload:
                prob.linear_constraints.add(
                    [cplex.SparsePair(ind=[varindex['DLoadFunction'],
                                           varindex[loadstr]],
                                      val=[1.0, -1.0])],
                    senses=['G'], rhs=[0],
                    names=['MaxDLoad.{}'.format(node)])


def addPathBinaryConstraints(prob, ppk):
    """

    :param prob:
    :param ppk:
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for k in ppk:
        for pi in xrange(len(ppk[k])):
            # prob.indicator_constraints.add(
            # cplex.SparsePair([varindex[_pv(k, pi)]], [1]),
            # indvar=varindex['binpath_{}_{}'.format(k.ID, pi)],
            #     sense='E', complemented=1, rhs=0)
            # prob.indicator_constraints.add(
            #     cplex.SparsePair([varindex[_pv(k, pi)]], [1]),
            #     indvar=varindex['binpath_{}_{}'.format(k.ID, pi)],
            #     sense='G', complemented=0, rhs=0)
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex[_pv(k, pi)],
                                   varindex['binpath_{}_{}'.format(k.ID, pi)]],
                                  [1, -1])],
                rhs=[0], senses='L')


def addRequireAllNodesConstraints(prob, ppk, nodes):
    """

    :param prob:
    :param ppk:
    :param nodes:
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for n in nodes:
        for k in ppk:
            for pi, path in enumerate(ppk[k]):
                if n in path:
                    # prob.indicator_constraints.add(
                    #     cplex.SparsePair(
                    #         [varindex['binpath_{}_{}'.format(k.ID, pi)]],
                    #         [1]),
                    #     indvar=varindex['binnode_{}'.format(n)],
                    #     sense='E', rhs=0, complemented=1)
                    prob.linear_constraints.add(
                        [cplex.SparsePair(
                            [varindex['binpath_{}_{}'.format(k.ID, pi)],
                             varindex['binnode_{}'.format(n)]],
                            [1, -1])],
                        rhs=[0], senses='L')


def addRequireAllEdgesConstraint(prob, ppk, edges):
    """

    :param prob:
    :param ppk:
    :param edges:
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for edge in edges:
        for k in ppk:
            for pi, path in enumerate(ppk[k]):
                pathedges = izip(path, path[1:])
                if edge in pathedges:
                    u, v = edge
                    # prob.indicator_constraints.add(
                    # cplex.SparsePair(
                    #         [varindex['binpath_{}_{}'.format(k.ID, pi)]],
                    #         [1]),
                    #     indvar=varindex['binedge_{}_{}'.format(u, v)],
                    #     sense='E', rhs=0, complemented=1)
                    prob.linear_constraints.add(
                        [cplex.SparsePair(
                            [varindex['binpath_{}_{}'.format(k.ID, pi)],
                             varindex['binedge_{}_{}'.format(u, v)]],
                            [1, -1])],
                        rhs=[0], senses='L')


def addRequireSomeNodesConstraints(prob, ppk):
    """

    :param prob:
    :param ppk:
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for k in ppk:
        for pi, path in enumerate(ppk[k]):
            var = [varindex['binpath_{}_{}'.format(k.ID, pi)]]
            mults = [-1]
            for n in path:
                var.append(varindex['binnode_{}'.format(n)])
                mults.append(1)
            prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                        senses=['G'], rhs=[0])


def addBudgetConstraint(prob, topology, func, bound):
    """

    :type topology: :py:class:`~panacea.optimization.topology.Topology`
    :param prob:
    :param topology:
    :param func:
    :param bound:
    """

    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    G = topology.getGraph()
    prob.linear_constraints.add(
        [cplex.SparsePair([varindex['binnode_{}'.format(n)]
                           for n in G.nodes_iter()],
                          [func(n) for n in G.nodes_iter()])
        ], senses=['L'], rhs=[bound(topology)
                              if hasattr(bound, '__call__') else bound],
        names=['Budget'])


# noinspection PyUnusedLocal
def addSymmetryConstraints(prob, ppk):
    # TODO: implement symmetric path constraints
    """

    :param prob:
    :param ppk:
    :raise NotImplementedError:
    """
    raise NotImplementedError()


def addFlowSplittingConstraints(prob, ppk):
    """

    :param prob:
    :param ppk:
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for k in ppk:
        var = []
        for pi, path in enumerate(ppk[k]):
            var.append(varindex['binpath_{}_{}'.format(k.ID, pi)])
        prob.linear_constraints.add(
            [cplex.SparsePair(var, [1] * len(var))],
            senses=['E'], rhs=[1],
            names=['flowsplit_{}'.format(k.ID)])


def addPowerConstraint(prob, nodeConsumption, edgeConsumption, normalize=True):
    """

    :param prob:
    :param nodeConsumption:
    :param edgeConsumption:
    :param normalize:
    """
    prob.variables.add(names=['linkpower', 'switchpower'], lb=[0, 0])
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    norm = sum(nodeConsumption.values()) + sum(edgeConsumption.values()) \
        if normalize else 1
    prob.linear_constraints.add([cplex.SparsePair(
        [varindex['binedge_{}_{}'.format(a, b)] for (a, b) in edgeConsumption] +
        [varindex['linkpower']],
        [edgeConsumption[link] / norm for link in edgeConsumption] + [-1])],
                                rhs=[0], senses=['E'])
    prob.linear_constraints.add([cplex.SparsePair(
        [varindex['binnode_{}'.format(u)] for u in nodeConsumption] +
        [varindex['switchpower']],
        [nodeConsumption[node] / norm for node in nodeConsumption] + [-1])],
                                rhs=[0], senses=['E'])


def addMinDiffConstraints(prob, prevSolution, epsilon=None, alpha=.5):
    """

    :param prob:
    :param prevSolution:
    :param epsilon:
    :param alpha:
    """
    names = [x for x in prevSolution if x.startswith('x')]
    if epsilon is None:
        epsdict = {}
        for x in names:
            _, a, b = x.split('_')
            # print a, b
            ep = 'd_{}_{}'.format(a, b)
            epsdict[x] = ep
        prob.variables.add(names=epsdict.values(),
                           lb=[0] * (len(epsdict)),
                           ub=[1] * (len(epsdict)))
        prob.variables.add(names=['maxdiff'], lb=[0], ub=[1])
        v = prob.variables.get_names()
        # print v
        varindex = dict(izip(v, range(len(v))))
        for x in names:
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex[x], varindex[epsdict[x]]],
                                  [1, -1])],
                rhs=[prevSolution[x]], senses='L')
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex[x], varindex[epsdict[x]]],
                                  [1, 1])],
                rhs=[prevSolution[x]], senses='G')
            prob.linear_constraints.add(
                [cplex.SparsePair(
                    [varindex['maxdiff'], varindex[epsdict[x]]],
                    [1, -1])],
                rhs=[0], senses='G')

        prob.objective.set_linear([(i, q * (1 - alpha)) for i, q in
                                   enumerate(prob.objective.get_linear())])
        prob.objective.set_linear(varindex['maxdiff'], alpha
        if prob.objective.get_sense() == prob.objective.sense.minimize else
        -alpha)
    else:
        prob.variables.set_lower_bounds(
            izip(names, [max(1, -epsilon + prevSolution[x])
                         for x in names]))
        prob.variables.set_upper_bounds(
            izip(names, [min(0, epsilon + prevSolution[x])
                         for x in names]))


def addFailedSwitchConstraints(prob, ppk, failedSwitches):
    """

    :param prob:
    :param ppk:
    :param failedSwitches:
    """
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    for k in ppk:
        for ind, path in enumerate(ppk[k]):
            for failedNode in failedSwitches:
                if failedNode in path:
                    prob.linear_constraints.add(
                        [cplex.SparsePair([varindex[_pv(k, ind)]], [1])],
                        rhs=[0], senses='E')


def generateFormulation(topology, ppk, resources=None, discreteResources=None,
                        objective=None, task=None,
                        constraints=None, budgetBound=None, budgetFunc=None,
                        allocationvals=None, saturatedcomm=None,
                        unsaturatedcomm=None, mipgap=None, timelimit=None,
                        diffFactor=0, **kwargs):
    """Generate the formulation based on the high-level configuration

    :param resources:
    :param discreteResources:
    :param objective:
    :param task:
    :param constraints:
    :param budgetBound:
    :param budgetFunc:
    :param allocationvals:
    :param saturatedcomm:
    :param unsaturatedcomm:
    :param mipgap:
    :param timelimit:
    :param topology: the topology on which we are running
    :param ppk: paths per commodity
    :param kwargs: all other keyword arguments
    """

    # Do a quick sanity check
    if task.lower() not in ['max', 'min', 'maximize', 'minimize']:
        raise InvalidConfigException('Unknown optimization task')

    if not resources:
        resources = []
    if not discreteResources:
        discreteResources = []
    # The topology graph
    topograph = topology.getGraph()

    # Do some sanity checks.
    # Make sure we have at least one path per commodity, otherwise this is
    # infeasible.
    for k in ppk:
        if not ppk[k]:
            raise NoPathsException('No paths for {}, commodity {}'.
                                   format(topology.name, k))

    # Initialize the CPLEX problem
    mainprob = startProblem()
    # Figure out types of constraints we have
    constraints = [x.lower() for x in constraints]
    # Adding basic decision variables
    addDecisionVariables(mainprob, ppk)
    # Now lets add all the binary decision variables
    bintypes = []
    if 'requireallnodes' in constraints or 'requiresomenodes' in constraints:
        bintypes.append('node')
        bintypes.append('path')
    if 'requirealledges' in constraints:
        bintypes.append('edge')
        bintypes.append('path')
    if 'dnodecap' in constraints or 'flowsplitting' in constraints:
        bintypes.append('path')
    # Now write  the binary variables
    # print bintypes
    addBinaryVariables(mainprob, ppk, topology, bintypes)
    if 'path' in bintypes:
        addPathBinaryConstraints(mainprob, ppk)

    # Now check for any other constraints
    # Write the routing cost
    if 'routingcost' in constraints:
        addRoutingCost(mainprob, ppk)
    if 'routeall' in constraints:
        addRouteAllConstraints(mainprob, ppk)
    # Setup our link constraints:
    if 'linkcap' in constraints:
        linkcaps = kwargs.get('linkcaps')
        if linkcaps is None:
            linkcaps = {}
            for link in topograph.edges_iter():
                u, v = link
                if 'capacity' in topograph.edge[u][v]:
                    linkcaps[link] = topograph.edge[u][v]['capacity']
        elif isinstance(linkcaps, int) or isinstance(linkcaps, float):
            linkcaps = {link: linkcaps for link in topograph.edges_iter()}
        elif hasattr(linkcaps, '__call__'):
            linkcaps = {link: linkcaps(topology, link) for link in
                        topograph.edges_iter()}
        elif isinstance(linkcaps, dict):
            pass
        addLinkConstraints(mainprob, ppk, linkcaps,
                           maxlink=(objective.lower() == 'maxlinkload'),
                           customFunc=kwargs.get('linkcapFunc'))

    def _parseNodeCaps(res):
        mycaps = Tree()
        for r in res:
            # print r
            s = '{}capacity'.format(r)
            tempcaps = kwargs.get(s)
            # print tempcaps
            if tempcaps is None:
                for node in topograph.nodes_iter():
                    if s in topograph.node[node]:
                        mycaps[node][r] = topograph.node[node][s]
            elif isinstance(tempcaps, int) or isinstance(tempcaps, float):
                for node in topograph.nodes_iter():
                    mycaps[node][r] = tempcaps
            elif hasattr(tempcaps, '__call__'):
                for node in topograph.nodes_iter():
                    mycaps[node][r] = tempcaps(topology, node)
            elif isinstance(tempcaps, dict):
                for node in tempcaps:
                    mycaps[node][r] = mycaps[node]
            else:
                raise InvalidConfigException('')
        return mycaps

    # Setup our node load for each node in the topology
    if 'nodecap' in constraints:
        caps = _parseNodeCaps(resources)
        addNodeCapacityConstraints(mainprob, ppk, caps,
                                   ('maxload' in objective))
    # Setup discrete loads on switches
    if 'dnodecap' in constraints:
        caps = _parseNodeCaps(discreteResources)
        addDiscreteLoadConstraints(mainprob, ppk, caps,
                                   ('maxdload' in objective))
    if 'requireallnodes' in constraints:
        addRequireAllNodesConstraints(mainprob, ppk, topograph.nodes())
    elif 'requiresomenodes' in constraints:
        addRequireSomeNodesConstraints(mainprob, ppk)
    if 'requirealledges' in constraints:
        addRequireAllEdgesConstraint(mainprob, ppk, topograph.edges())
    if 'flowsplitting' in constraints:
        addFlowSplittingConstraints(mainprob, ppk)
    if 'budget' in constraints:
        addBudgetConstraint(mainprob, topology, budgetFunc,
                            budgetBound)
    if 'power' in constraints:
        nc = {n: kwargs.get('switchPower') for n in topograph.nodes_iter()}
        ec = {e: kwargs.get('linkPower') for e in topograph.edges_iter()}
        # print ec
        addPowerConstraint(mainprob, nc, ec, normalize=True)
    if 'allocation' in constraints:
        unsat = unsaturatedcomm
        if unsat is not None:
            addAllocateFlowConstraints(mainprob, ppk, unsat, setEqual=True)
            sat = saturatedcomm
            if sat is not None and sat:
                assert len(saturatedcomm) == len(allocationvals)
                if allocationvals is None:
                    raise InvalidConfigException('Allocation values required')
                for index in xrange(len(allocationvals)):
                    addAllocateFlowConstraints(mainprob, ppk, sat[index],
                                               allocationvals[index],
                                               setEqual=True)
        else:
            addAllocateFlowConstraints(mainprob, ppk, ppk.keys(), setEqual=True)
    elif 'demand' in constraints:
        addAllocateFlowConstraints(mainprob, ppk, ppk.keys(), setEqual=False)

    if isinstance(objective, dict):
        setObjective(mainprob, objective, task)
    else:
        if objective.lower() == 'routingcost':
            setObjective(mainprob, {'RoutingCost': 1}, task)
        elif objective.lower() == 'maxload':
            setObjective(mainprob, {'LoadFunction': 1}, task)
        elif objective.lower() == 'maxlinkload':
            setObjective(mainprob, {'LinkLoadFunction': 1}, task)
        elif objective.lower() == 'maxloadmaxdload':
            setObjective(mainprob, {'LoadFunction': 1, 'DLoadFunction': 1},
                         task)
        elif objective.lower() == 'power':
            setObjective(mainprob, {'linkpower': 1,
                                    'switchpower': 1}, task)
        elif objective.lower() == 'allocation':
            d = {n: 1 for n in mainprob.variables.get_names()
                 if n.startswith('allocation')}
            setObjective(mainprob, d, task)
        elif objective.lower() == 'throughput':
            d = {n: 1 / topology.getNumFlows()
                 for n in mainprob.variables.get_names()
                 if n.startswith('allocation')}
            setObjective(mainprob, d, task)
        else:
            raise InvalidConfigException('Unknown objective')
    if 'mindiff' in constraints:
        prevSolution = kwargs.get('prevSolution')
        addMinDiffConstraints(mainprob, prevSolution, alpha=diffFactor)

    if mipgap is not None:
        mainprob.parameters.mip.tolerances.mipgap.set(mipgap)
    mainprob.set_log_stream(None)
    mainprob.set_results_stream(None)
    if timelimit is not None:
        mainprob.parameters.timelimit.set(timelimit)
    return mainprob


def _MaxMinFairness_mcf(topology, unsat, sat, alloc, ppk):
    """ Formulate and solve a multi-commodity flow problem given the saturated
        and un-saturated commodities

    :param topology
    :returns: allocations and the cplex solved problem (for variable access)"""
    prob = generateFormulation(topology, ppk, constraints=['allocation'],
                               objective='allocation', task='max',
                               unsaturatedcomm=unsat, saturatedcomm=sat,
                               allocationvals=alloc)
    prob.solve()
    alloc = prob.solution.get_objective_value()
    return alloc, prob


def iterateMaxMinFairness(topology, ppk):
    """ Run the iterative algorithm for max-min fairness

       ..warning:: This implementation does not use any optimizations
           like binary search

       :param topology: the topology on which we are running this
       :param ppk: paths per commodity
       :return: a tuple: solved CPLEX problem and a dict containing
           allocation values per commodity
       :rtype: tuple
    """
    commoditiesSAT = defaultdict(lambda: [])
    commoditiesUNSAT = set(ppk.keys())
    prob = None
    t = []  # allocation values per each iteration
    i = 0  # iteration index
    while commoditiesUNSAT:
        print i,
        alloc, prob = _MaxMinFairness_mcf(topology, commoditiesUNSAT,
                                          commoditiesSAT, t, ppk)
        if not prob.solution.get_status() == 1:
            raise UnsupportedOperationException('No solution to the problem')
        t.append(alloc)
        # Check if commodity is saturated, if so move it to saturated list
        for k in list(commoditiesUNSAT):
            # FIXME: this is a very inefficient non-blocking test
            dual = prob.solution.get_dual_values('Demand.k.{}'.format(k.ID))
            if dual > 0:
                commoditiesUNSAT.remove(k)
                commoditiesSAT[i].append(k)
        i += 1
    print i
    # Simplify the result
    result = {}
    for j in xrange(len(t)):
        for k in commoditiesSAT[j]:
            result[k] = t[j]
    return prob, result
