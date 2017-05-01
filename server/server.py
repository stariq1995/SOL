import argparse
import logging

import flask
import numpy
from attrdict import AttrDict
from flask import Flask, request, jsonify
from flask import abort
from flask import send_from_directory
from flask_compress import Compress
from sol.opt.composer import compose
from sol.path.generate import generate_paths_ie
from sol.path.paths import PPTC
from sol.path.predicates import null_predicate
from sol.topology.topologynx import Topology
from sol.topology.traffic import TrafficClass

from sol.opt.app import App

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


def assign_to_tc(tcs, paths, name):
    """
    Assign paths to traffic classes based on the ingress & egress nodes.
    To be used only if there is one traffic class (predicate)
    per ingress-egress pair.

    :param tcs: list of traffic classes
    :param paths: dictionary of paths: ..

            paths[ingress][egress] = list_of_paths

    :return: paths per traffic class
    """
    pptc = PPTC()
    for tc in tcs:
        pptc.add(name, tc, paths[tc.ingress()][tc.egress()])
    return pptc


@app.route('/')
@app.route('/api/v1/hi')
def hi():
    """
    A simple greeting to ensure the server is up

    """
    return u"Hello, this is SOL API version {}".format(__API_VERSION)


@app.route('/api/v1/compose_apps', methods=['POST'])
def composeview():
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

    # TODO: take predicate into account
    apps = []
    for aj in apps_json:
        aj = AttrDict(aj)
        tcs = []
        for tcj in aj.traffic_classes:
            tc = TrafficClass(tcj.tcid, u'tc', tcj.src, tcj.dst,
                              numpy.array([tcj.vol_flows]))
            tcs.append(tc)

        pptc = assign_to_tc(tcs, _paths, aj.id)
        # pptc = generate_paths_tc(topology, tcs, _predicatedict[aj.predicate], 20,
        #                          float('inf'), name=aj.id)
        # objective
        if aj.objective.get('resource') is None:
            objective = (aj.objective.name)
        else:
            objective = (aj.objective.name, aj.objective.resource)

        # resource_cost
        resource_cost = {r.resource: r.cost for r in map(AttrDict, aj.resource_costs)}
        apps.append(App(pptc, list(aj.constraints), resource_cost, objective, name=aj.id))
    fairness_mode = data.get('fairness', 'weighted')
    opt = compose(apps, topology, obj_mode=fairness_mode,
                  globalcaps=[AttrDict(resource=r, cap=1) for r in resource_cost.keys()])
    opt.solve()
    result = []
    for app in apps:
        result_app = {"app": app.name, "tcs": []}
        result_pptc = opt.get_paths(0)
        for tc in app.pptc:
            obj = {
                "tcid": tc.ID,
                "paths": []
            }
            for p in result_pptc[tc]:
                if p.flow_fraction() != 0:
                    obj["paths"].append({
                        "nodes": p.nodes().tolist(),
                        "fraction": p.flow_fraction()
                    })
            result_app["tcs"].append(obj)
        result.append(result_app)
    logger.debug(result)
    return jsonify(result)


@app.route('/api/v1/topology/', methods=['GET', 'POST'])
def topology():
    """
    Set or return the stored topology

    """
    global _topology, _paths
    if request.method == 'GET':
        if _topology is None:
            return
        return jsonify(_topology.to_json())
    elif request.method == 'POST':
        data = request.get_json()
        logger.debug(data)
        _topology = Topology.from_json(data)
        logging.info('Topology read successfully')
        _paths = {}
        for s in _topology.nodes():
            _paths[s] = {}
            for t in _topology.nodes():
                _paths[s][t] = list(generate_paths_ie(s, t, _topology, null_predicate, 100, 5))
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
