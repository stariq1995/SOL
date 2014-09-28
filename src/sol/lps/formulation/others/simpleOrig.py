"""
Original SIMPLE implementation from the paper

Since this is similar to the pathbased formulation already, we are reusing
"our" functions
"""
from collections import defaultdict
from itertools import izip

from panacea.lps import apps
from panacea.util.exceptions import FormulationException
from panacea.util.pythonHelper import Tree


__author__ = 'Victor H.'

import cplex
import time

import panacea.lps.formulation.generateFormulation as gf
import panacea.lps.commonConfig as cc


def runSIMPLEOrig(topology, ppk, resources, coverage, write=False, lp=False):
    """  RUN THIS
    :param resources:
    :param coverage:
    :param write:
    :param topology:
    :param ppk:
    :return:
    """
    prob = _generateFormulationSIMPLEOrigILP(topology, ppk, apps.apps[
        'SIMPLE']['tcamcapacity'], coverage, lp=lp)
    if write:
        prob.write('simple_ilp.lp')
    dur = 0
    start = time.time()
    prob.solve()
    dur += time.time() - start
    if prob.solution.get_status() not in cc.solcodesGood:
        raise FormulationException('could not solve SIMPLE ILP')
    # Get the pruned paths
    newppk = defaultdict(lambda: [])
    commindex = {k.ID: k for k in ppk}
    for name, val in izip(prob.variables.get_names(),
                          prob.solution.get_values()):
        if val == 1:
            _, comm, pathind = name.split('_')
            k = commindex[int(comm)]
            newppk[k].append(ppk[k][int(pathind)])
    prob = _generateFormulationSIMPLEOrig(topology, newppk, resources)
    if write:
        prob.write('simple_lp.lp')
    start = time.time()
    prob.solve()
    dur += time.time() - start
    if prob.solution.get_status() not in cc.solcodesGood:
        raise FormulationException('could not solve SIMPLE ILP')
    return prob, dur, newppk


def _generateFormulationSIMPLEOrig(topology, ppk, resources):
    prob = cplex.Cplex()
    gf.addDecisionVariables(prob, ppk)
    gf.addRouteAllConstraints(prob, ppk)
    caps = Tree()
    topograph = topology.getGraph()
    for node in topograph.nodes_iter():
        for r in resources:
            s = '{}capacity'.format(r)
            if s in topograph.node[node]:
                caps[node][r] = topograph.node[node][s]
    gf.addNodeCapacityConstraints(prob, ppk, caps, True)
    gf.setObjective(prob, {'LoadFunction': 1.0}, 'min')
    return prob


def _generateFormulationSIMPLEOrigILP(topology, ppk, tcamCap, coverage, lp):
    G = topology.getGraph()
    prob = cplex.Cplex()
    var = ['binpath_{}_{}'.format(k.ID, pi) for k in ppk
           for pi in xrange(len(ppk[k]))]
    prob.variables.add(names=var,
                       types=[prob.variables.type.continuous if lp else
                              prob.variables.type.binary] * len(var),
                       lb=[0] * len(var),
                       ub=[1] * len(var)
    )
    prob.variables.add(names=['mboxused_{}'.format(node) for node in
                              G.nodes_iter() if topology.isMiddlebox(node)],
                       lb=[0] * topology.getNumNodes('middlebox'))
    prob.variables.add(names=['maxmboxoccurs'], lb=[0])
    v = prob.variables.get_names()
    varindex = dict(izip(v, range(len(v))))
    # coverage
    for k in ppk:
        prob.linear_constraints.add([cplex.SparsePair(
            [varindex['binpath_{}_{}'.format(k.ID, ind)] for ind in
             xrange(len(ppk[k]))], [1] * len(ppk[k]))],
                                    rhs=[min(coverage, ppk[k])], senses='G',
                                    names=['coverage.k.{}'.format(k.ID)])
    for node in G.nodes_iter():
        var = []
        mults = []
        if topology.isSwitch(node):
            for k in ppk:
                for pi, path in enumerate(ppk[k]):
                    # rules
                    if node in path:
                        var.append(varindex['binpath_{}_{}'.format(k.ID, pi)])
                        mults.append(path.getNodes().count(node))
            prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                        senses='L', rhs=[tcamCap],
                                        names=['SwitchRules.{}'.format(node)])
        elif topology.isMiddlebox(node):
            for k in ppk:
                for pi, path in enumerate(ppk[k]):
                    # mboxoccurs
                    if node in path:
                        var.append(varindex['binpath_{}_{}'.format(k.ID, pi)])
                        mults.append(1)
            var.append(varindex['mboxused_{}'.format(node)])
            mults.append(-1)
            prob.linear_constraints.add([cplex.SparsePair(var, mults)],
                                        senses='E', rhs=[0], names=[
                    'mbox.{}'.format(node)])
            prob.linear_constraints.add(
                [cplex.SparsePair([varindex['maxmboxoccurs'],
                                   varindex['mboxused_{}'.format(node)]],
                                  [1, -1])], rhs=[0], senses='G')
    prob.objective.set_linear(varindex['maxmboxoccurs'], 1.0)
    prob.objective.set_sense(prob.objective.sense.minimize)
    return prob
