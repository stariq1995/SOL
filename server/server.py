import argparse

import flask
import logging

import numpy
from attrdict import AttrDict
from flask import Flask, request, jsonify
from flask import abort
from flask import send_from_directory
from flask_compress import Compress
from sol.opt.app import App
from sol.path.generate import generate_paths_tc
from sol.path.predicates import null_predicate
from sol.topology.topologynx import Topology
from sol.topology.traffic import TrafficClass
from logging import Logger,INFO
from sol.opt.composer import compose

app = Flask(__name__)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())

# REST-specific configuration here
__API_VERSION = 1  # the current api version
_json_pretty = False  # whether to pretty print json or not (not == save space)
_gzip = True  # whether to gzip the returned responses

_topology = None


_predicatedict = {
    'null': null_predicate,
    'null_predicate': null_predicate,
}

def assign_to_tc(tcs, paths):
    """
    Assign paths to traffic classes based on the ingress & egress nodes.
    To be used only if there is one traffic class (predicate)
    per ingress-egress pair.

    :param tcs: list of traffic classes
    :param paths: dictionary of paths: ..

            paths[ingress][egress] = list_of_paths

    :return: paths per traffic class
    """
    pptc = {}
    for tc in tcs:
        pptc[tc] = paths[tc.ingress()][tc.egress()]
    return pptc


@app.route('/')
@app.route('/api/v1/hi')
def hi():
    """
    A simple greeting to ensure the server is up

    """
    return u"Hello, this is SOL API version {}".format(__API_VERSION)


@app.route('/api/v1/compose', methods=['POST'])
def compose():
    """
    Create a new composed opimization, solve and return the

    :return:

    """
    try:
        data = request.get_json()
        logger.debug(data)
        apps_json = data['apps']
        topology = Topology.from_json(data['topology'])
    except KeyError:  # todo: is this right exception?
        abort(400)

    # TODO: load paths from disk based on predicates and topology
    # For now, extract list of predicates and generate paths for them
    # on the fly. Will be slower.
    # all_predicates = set()
    # for aj in apps_json:
    #     all_predicates.add(aj["predicate"])
    apps = []
    for aj in apps_json:
        aj = AttrDict(aj)
        tcs = []
        for tcj in aj.traffic_classes:
            tc = TrafficClass(tcj.tcid, u'tc', tcj.src, tcj.dst,
                              numpy.ndarray([tcj.vol_flows]))
            tcs.append(tc)

        pptc = generate_paths_tc(topology, tcs, _predicatedict[aj.predicate], 100,
                                 float('inf'))
        # constraints
        constraints = [(c.name) for c in aj.constraints]
        # objective
        if aj.objective.get('resource'):
            objective = (aj.objective.name)
        else:
            objective = (aj.objective.name, aj.objective.resource)

        # resource_cost
        resource_cost = {r.name: r.cost for r in aj["resource_costs"]}
        apps.append(App(pptc, constraints, resource_cost, objective, name=aj.id))
    fairness_mode = data.get('fairness', 'weighted')
    opt = compose(apps, topology, obj_mode=fairness_mode,
                  globalcaps={r: 1 for r in resource_cost.keys()})
    opt.solve()
    result = {}
    for app in apps:
        result[app.name] = {"app": app.name,
                            "tcs": []}
        result_pptc = opt.get_path_fractions(app.pptc)
        for tc in result_pptc:
            obj = {
                "tcid": tc.id,
                "paths": []
            }
            for p in result_pptc[tc]:
                obj["paths"].append({
                    "nodes": p.nodes(),
                    "fraction": p.fraction()
                })
            result[app.name]["tcs"].append(obj)
    return jsonify(result)


@app.route('/api/v1/topology/', methods=['GET', 'POST'])
def topology():
    """
    Set or return the stored topology

    """
    global _topology
    if request.method == 'GET':
        if _topology is None:
            return
        return jsonify(_topology.to_json())
    elif request.method == 'POST':
        data = request.get_json()
        logger.debug(data)
        _topology = Topology.from_json(data)
        logging.info('Topology read successfully')
        return ""
    else:
        abort(405)  # method not allowed


@app.route('/apidocs/')
def docs(path='index.html'):
    """
    Endpoint for swagger UI
    :param path:
    :return:
    """
    return send_from_directory('static/swaggerui/', path)


@app.route('/spec')
def swagger_json():
    """
    Endpoint that returns the swagger api using JSON
    :return:
    """
    with open('static/api.json', 'r') as f:
        return jsonify(flask.json.loads(f.read()))
        # return url_for('static', filename='api.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path-dir', required=False)
    parser.add_argument('--dev', action='store_true')
    parser.add_argument('--debug', action='store_true')
    options = parser.parse_args()

    if options.dev:
        _json_pretty = True
        _gzip = False

    if _gzip:
        c = Compress()
        c.init_app(app)
    if options.debug:
        logger.setLevel(logging.DEBUG)
    app.run(debug=options.dev)
