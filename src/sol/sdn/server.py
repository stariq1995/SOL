import argparse

from flask import Flask, request, jsonify
from flask import abort
from flask_autodoc import Autodoc
from flask_compress import Compress
from sol.topology.topologynx import Topology

app = Flask(__name__)
doc = Autodoc(app)

# REST-specific configuration here
__API_VERSION = 1  # the current api version
_json_pretty = False  # whether to pretty print json or not (not == save space)
_gzip = True  # whether to gzip the returned responses

_topology = None


@app.route('/')
@app.route('/api/v1/hi')
@doc.doc()
def hi():
    """
    A simple greeting to ensure the server is up

    """
    return u"Hello, this is SOL API version {}".format(__API_VERSION)


@app.route('/api/v1/compose')
@doc.doc()
def compose(apps, mode, epoch_mode='max', fairness_mode='weighted'):
    abort(501)  # not implemented yet


@app.route('/api/v1/topology/', methods=['GET', 'POST'])
@doc.doc()
def topology():
    """ Set or return the stored topology """
    global _topology
    if request.method == 'GET':
        return jsonify(_topology.to_json())
    elif request.method == 'POST':
        _topology = Topology.from_json(request.data)
    else:
        abort(405)  # method not allowed


@app.route('/doc')
@app.route('/docs')
def docs():
    return doc.generate()


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
