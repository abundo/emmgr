#!/usr/bin/env python3

'''
Implements an API for emmgr

All responses are JSON encoded
'''

from flask import Flask, jsonify, request
from app import app

import emmgr.lib.element as element

# ----------------------------------------------------------------------------
#  Configuration
# ----------------------------------------------------------------------------

@app.route('/api/em/get_running_config/<hostname>/<model>', methods=['GET'])
def get_running_config(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        conf = e.get_running_config()
        return jsonify( { 'result': conf })
    except element.ElementException as err:
        return "%s" % err, 404

@app.route('/api/em/save_running_config/<hostname>/<model>', methods=['GET'])
def save_running_config(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        conf = e.save_running_config()
        return jsonify( { 'result': conf })
    except element.ElementException as err:
        return "%s" % err, 404


@app.route('/api/em/configure/<hostname>/<model>', methods=['POST'])
def configure(hostname, model):
    try:
        config_lines = request.form.get('config_lines')
        save_running_config = request.form.get('save_running_config')
        e = element.Element(hostname=hostname, model=model)
        conf = e.configure(config_lines, save_running_config)
        return jsonify( { 'result': conf })
    except element.ElementException as err:
        return "%s" % err, 404

# ----------------------------------------------------------------------------
#  Commands
# ----------------------------------------------------------------------------

@app.route('/api/em/run/<hostname>/<model>/<cmd>', methods=['GET'])
def run(hostname, model, cmd):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404


@app.route('/api/em/reload/<hostname>/<model>/<save_config>', methods=['GET'])
def reload(hostname, model, save_config=True):
    try:
        e = element.Element(hostname=hostname, model=model)
        conf = e.reload(save_config=save_config)
        return jsonify( { 'result': conf })
    except element.ElementException as err:
        return "%s" % err, 404

# ----------------------------------------------------------------------------
#  Software
# ----------------------------------------------------------------------------

def sw_copy_to(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.sw_copy_to(mgr, filename, dest_filename, callback)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404

def sw_delete(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404

def sw_delete_unneeded(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404

def sw_exist(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404

def sw_list(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404

def sw_set_boot(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404

def sw_upgrade(hostname, model):
    try:
        e = element.Element(hostname=hostname, model=model)
        output = e.run(cmd)
        return jsonify( { 'result': output })
    except element.ElementException as err:
        return "%s" % err, 404


# ----------------------------------------------------------------------------
#  Other
# ----------------------------------------------------------------------------

@app.route('/api/em/models', methods=['GET'])
def get_element_models():
    items = []
    items.append( {"model": "ASR920",   "search": "%ASR-920%"} )
    items.append( {"model": "C4500",    "search": "%4506%"} )
    items.append( {"model": "HP A5500", "search": "%HP A5500%"} )
    items.append( {"model": "ME3400",   "search": "%ME-3400%"} )
    items.append( {"model": "MS4000",   "search": "%MS40%"} )
    items.append( {"model": "RS5128",   "search": "%5128%"} )
    items.append( {"model": "S5700",    "search": "%S570%"} )
    return jsonify( { "items": items } )


if __name__ == '__main__':
    """
    For development, run API standalone
    """
    app.run(debug=True)
