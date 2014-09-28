#!/usr/bin/env python

""" This script converts old vyas-style tm to a traffic matrix class"""

import argparse
from collections import defaultdict

import numpy as np

from ..lps.topology.traffic import TrafficMatrix


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    parser.add_argument('-o', '--outfile', required=True)
    parser.add_argument('--format', choices=['yaml', 'pickle'], default='yaml')

    options = parser.parse_args()

    d = defaultdict(lambda: [])
    for fname in options.files:
        with open(fname, 'r') as f:
            for line in f:
                fields = line.split()
                d[(int(fields[0]), int(fields[-2]))].append(float(fields[-1]))
    for k, v in d.items():
        d[k] = np.mean(v)
    tm = TrafficMatrix(dict(d))

    with open(options.outfile, 'w') as o:
        if options.format == 'yaml':
            tm.dumpToYAML(o)
        elif options.format == 'pickle':
            tm.dumpToPickle(o)
        else:
            raise Exception('Unknown save format')
