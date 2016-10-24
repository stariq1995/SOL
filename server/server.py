import argparse

import flask
from flask import Flask, request, jsonify
from flask import abort
from flask import send_from_directory
from flask import url_for
from flask_compress import Compress
from sol.opt.app import App
from sol.topology.topologynx import Topology

app = Flask(__name__)

# REST-specific configuration here
__API_VERSION = 1  # the current api version
_json_pretty = False  # whether to pretty print json or not (not == save space)
_gzip = True  # whether to gzip the returned responses

_topology = None


@app.route('/')
@app.route('/api/v1/hi')
def hi():
    """
    A simple greeting to ensure the server is up

    """
    return u"Hello, this is SOL API version {}".format(__API_VERSION)


@app.route('/api/v1/compose')
def compose(data, apps, mode, fairness_mode='weighted'):
    """
    Create a new composed opimization and return
    :param apps:
    :param mode:
    :param fairness_mode:
    :return:

    """
    try:
        data = request.json
    except 
    tc = data['tc']
    apps = [App(**a) for a in data['apps']]
    mode = data['mode']
    epoch_mode = data.get('fairness', 'weighted')
    abort(501)  # not implemented yet


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
        _topology = Topology.from_json(request.data)
        return
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
    options = parser.parse_args()

    if options.dev:
        _json_pretty = True
        _gzip = False

    if _gzip:
        c = Compress()
        c.init_app(app)
    app.run(debug=options.dev)
