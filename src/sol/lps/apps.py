""" App configurations """
from panacea.lps.path.predicates import SIMPLEModifier

apps = {
    # 'MCF': {
    #     'constraints': ['linkcap', 'routeall'],
    #     'objective': 'routingcost',
    #     'task': 'minimize',
    #     'predicate': 'nullPredicate',
    #     'pruneStrategy': 'shortest',
    #     'pruneNumber': '5x',  # 5 paths per commodity
    # },
    'SIMPLE': {
        'constraints': ['linkcap', 'nodecap', 'dnodecap', 'routeall'],
        'objective': 'maxload',
        'task': 'minimize',
        'resources': ['cpu'],
        'discreteResources': ['tcam'],
        # 'cpucapacity': 2.2 * (10**6),
        # 'tcamcapacity': lambda x: (x.getNumNodes('switch') ** 2) * 5,
        'tcamcapacity': 2000,
        'pairparams': {'minShortestPath': 1, 'minDegree': 1, 'hasSinks': False},
        'predicate': 'SIMPLEPredicate',
        'trafficModel': 'normal',
        #'trafficMatrix': 'object or file',
        'pruneStrategy': 'random',
        'pruneNumber': '5x',
        'pathModifyFunc': SIMPLEModifier
    },
    'SIMPLE-Merlin': {
        'appalt': 'SIMPLE',
        'constraints': ['linkcap', 'routeall'],
        'objective': 'maxlinkload',
        'task': 'minimize',
        'resources': [],
        'discreteResources': [],
        # 'cpucapacity': 2.2 * (10**6),
        # 'tcamcapacity': lambda x: (x.getNumNodes('switch') ** 2) * 5,
        'tcamcapacity': 2000,
        'pairparams': {'minShortestPath': 1, 'minDegree': 1, 'hasSinks': False},
        'predicate': 'SIMPLEPredicate',
        'trafficModel': 'normal',
        #'trafficMatrix': 'object or file',
        'pruneStrategy': 'random',
        'pruneNumber': '5x',
        # 'pathModifyFunc': SIMPLEModifier
    },
    # 'Merlin': {
    #     'constraints': ['linkcap', 'routeall'],
    #     'resources': [],
    #     'task': 'minimize',
    #     'objective': 'maxlinkload',
    #     'pairparams': {'minShortestPath': 2, 'minDegree': 1, 'hasSinks': True},
    #     'predicate': 'merlinPredicate',
    #     'pruneStrategy': 'shortest',
    #     'pruneNumber': '15x',
    #     'mipgap': 0.1,
    #     'trafficModel': 'uniform',
    #     'timelimit': 600
    # },
    'Panopticon': {
        'constraints': ['requireSomeNodes', 'dnodecap', 'budget', 'routeall',
                        'routingCost'],
        'objective': 'routingcost',
        'resources': [],
        'task': 'minimize',
        'dresources': ['tcam'],
        'tcamcapacity': 2000,
        'pairparams': {'minShortestPath': 1, 'minDegree': 1, 'hasSinks': False},
        'predicate': 'nullPredicate',
        'budgetFunc': lambda node: 1,
        'budgetBound': lambda topo: topo.getNumNodes('switch'),
        'trafficModel': 'normal',
        'pruneStrategy': 'shortest',
        'pruneNumber': '5x'
    },
    # 'NIPS': {
    #     'constraints': ['linkcap', 'nodecap', 'routeall'],
    #     'objective': 'maxload',
    #     'task': 'min',
    #     'resources': ['cpu', 'mem'],
    #     'cpucapacity': 2.2 * (10 ** 6),
    #     'memcapacity': 4 * (10 ** 9),
    #     'dresources': [],
    #     'linkcapFunc': funcs.curryLinkConstraintFunc(
    #         funcs.dropUpstreamLinkFunc, linkcaps={}, dropRates={},
    #         cumulative=False),  # insert appropriate dict values
    #     'pairparams': {'minShortestPath': 2, 'minDegree': 1, 'hasSinks': True},
    #     'predicate': 'redundantNIPSPredicate',
    #     'classNames': ['regular'],
    #     'trafficModel': 'uniform',
    #     'pruneStrategy': 'random'
    # },
    'Elastic': {
        'constraints': ['linkcap', 'routeall', 'requireAllNodes',
                        'requireAllEdges', 'power'],
        'objective': 'power',
        'task': 'min',
        'resources': [],
        'dresources': [],
        'pairparams': {},
        'predicate': 'nullPredicate',
        'overprovision': 3,
        'trafficModel': 'uniform',
        # 'timelimit': 300,
        'switchPower': 200,
        'linkPower': 100,
        'pruneStrategy': 'shortest',
        'pruneNumber': '5x'
    },
    'SWAN': {
        # 'constraints': ['link', 'allocation'],
        'constraints': ['link', 'demand'],
        # 'objective': 'mmf',
        'objective': 'throughput',
        'task': 'max',
        'trafficClasses': ['highpri', 'mediumpri', 'lowpri'],
        'resources': [],
        'dresources': [],
        'pairparams': {'minShortestPath': 1, 'minDegree': 1, 'hasSinks': False},
        'overprovision': .5,
        'predicate': 'nullPredicate',
        'trafficModel': 'normal',
        # 'timelimit': 300
        'pruneStrategy': 'shortest',
        'pruneNumber': '15x'
    }
}
