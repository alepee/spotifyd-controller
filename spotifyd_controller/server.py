from json import dumps
from flask import Flask, request, make_response, jsonify, render_template
from string import Template

from .registry import REGISTRY
from .actions import ACTIONS

server = Flask(__name__)

@server.route("/")
def index():
    return render_template('index.html')

@server.route("/api/")
def api_index():
    return 'Ok'

@server.route("/api/latest/")
def latest():
    tag = tag_reader_ref.ask('latest', timeout=1)

    app.logger.debug('Returning latest tag %s', tag)

    if tag is None:
        data = {
            'success': False,
            'message': 'No tag scanned yet'
        }

    else:
        data = {
            'success': True,
            'message': 'Scanned tag found',
        }

        data.update(tag.as_dict(include_scanned=True))

    resp = make_response(jsonify(data))
    resp.headers['Content-Type'] = 'application/json'
    
    return resp

@server.route("/api/registry/")
def registry():
    tags_list = []

    for tag in REGISTRY.values():
        tags_list.append(tag.as_dict())

    data = {
        'success': True,
        'message': 'Registry successfully read',
        'tags': tags_list
    }

    resp = make_response(jsonify(data))
    resp.headers['Content-Type'] = 'application/json'
    
    return resp

@server.route("/api/register/", methods=['POST', 'PUT'])
def register():
    try:
        tag = REGISTRY.register(
            action_class=request.form['action-class'],
            uid=request.form['uid'],
            alias=request.form['alias'],
            parameter=request.form['parameter'],
        )

        data = {
            'success': True,
            'message': 'Tag successfully registered',
        }

        data.update(tag.as_dict())
        resp = make_response(jsonify(data))

    except ValueError as exception:
        data = {
            'success': False,
            'message': str(exception)
        }
        resp = make_response(jsonify(data), 400)

    resp.headers['Content-Type'] = 'application/json'
    
    return resp

@server.route("/api/unregister/", methods=['POST', 'PUT'])
def unregister():
    try:
        REGISTRY.unregister(uid=request.form['uid'])

        data = {
            'success': True,
            'message': 'Tag successfully unregistered',
        }
        resp = make_response(jsonify(data))

    except KeyError as ex:
        data = {
            'success': False,
            'message': Template('Unknown tag "$uid"').substitute(uid = request.form['uid'])
        }
        resp = make_response(jsonify(data), 400)

    except ValueError as ex:
        data = {
            'success': False,
            'message': str(ex)
        }
        resp = make_response(jsonify(data), 400)

    resp.headers['Content-Type'] = 'application/json'
    
    return resp

@server.route("/api/action-classes/")
def action_classes():
    data = {
        'success': True,
        'message': 'Action classes successfully retreived',
        'action_classes': ACTIONS
    }

    resp = make_response(jsonify(data))
    resp.headers['Content-Type'] = 'application/json'
    
    return resp
