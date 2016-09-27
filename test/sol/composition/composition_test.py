# coding=utf-8
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
from __future__ import print_function
import numpy
import pytest
import tmgen

from sol.opt.app import App
from sol.opt.composer import _detect_cost_conflict, CompositionError

# paramertize with different topology sizes
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.topology.generators import complete_topology
from sol.topology.provisioning import traffic_classes


@pytest.fixture(params=[5, 8])
def pptc(request):
    # get a complete topology
    topo = complete_topology(request.param)
    # generate a dummy TM and traffic classes
    tm = tmgen.uniform_tm(request.param, 20, 50, 1)
    tc = traffic_classes(tm, {u'all': 1}, {u'all': 10})
    # generate all possibe paths
    res = generate_paths_tc(topo, tc, null_predicate, 10, numpy.inf)
    return res

def test_ResourceConflictDetection(pptc):
    a1 = App(pptc, [], {'r1': 200, 'r2': 300})
    a2 = App(pptc, [], {'r1': 200, 'r2': 300, 'r3': 500})
    print(_detect_cost_conflict([a1, a2]))
    print(_detect_cost_conflict([a1]))
    print(_detect_cost_conflict([]))
    # with pytest.raises(TypeError):
    #     _detect_cost_conflict({})
    a1 = App(pptc, [], {'r1': 200, 'r2': 300})
    a2 = App(pptc, [], {'r1': 200, 'r2': 1, 'r3': 500})
    with pytest.raises(CompositionError):
        print(_detect_cost_conflict([a1, a2]))