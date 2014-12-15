def main():
    config = {
    'name': 'ElasticTree'
            'constraints': ['linkcap', 'routeallflow', 'requireAllNodes',
                            'requireAllEdges'],
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
    }
    # define custom power variables
    pro


if __name__ == '__main__':
    main()
