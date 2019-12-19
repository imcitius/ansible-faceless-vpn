#!/usr/bin/env python
from __future__ import print_function
import base64
import os
import sys
import json
from collections import OrderedDict
import requests
import re
import traceback

vm_prefix = [
    'vsphere_virtual_machine.host'
]

tf_state_path = os.environ['TF_STATE_PATH']
project = os.environ['ANSIBLE_PROJECT']

if tf_state_path == '' or project == '':
  sys.stderr.write('TF state path or ansible project name not specified\n')
  sys.exit(1)

def _init_inventory():
    return OrderedDict({
        "all": {
            "hosts": [],
            "vars": {
                'project': project
            },
            "children": []
        },
        "_meta": {
            "hostvars": {}
        }
    })


def is_vm(name):
    for pref in vm_prefix:
        if name.startswith(pref):
            return True
    return False


def _get_outputs(current_module, modules):
    if len(current_module['path']) == 1:
        return []

    if len(current_module['outputs']) != 0:
        return current_module['outputs']

    path = current_module['path']
    parent_path = path[:-1]

    parent = None
    for module in modules:
        if module['path'] == parent_path:
            parent = module

    return _get_outputs(parent, modules)

def _is_ip_private(ip):

    # https://en.wikipedia.org/wiki/Private_network

    priv_lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    priv_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
    priv_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")

    res = priv_lo.match(ip) or priv_24.match(ip) or priv_20.match(ip) or priv_16.match(ip)
    return res is not None

def _processing(tfstate, inventory):
    if 'modules' not in tfstate:
        raise KeyError("modules not found in tfstate")

    modules = tfstate["modules"]
    for module in modules:
        if 'path' not in module:
            raise KeyError("path not found in module %s" % json.dumps(module))
        if 'outputs' not in module:
            raise KeyError("outputs not found in module %s" % json.dumps(module))

        if len(module['path']) == 1:
            continue

        outputs = _get_outputs(module, modules)

        if 'meta' not in outputs:
            raise KeyError("outputs has no meta in module %s" % json.dumps(module))

        if 'value' not in outputs['meta']:
            raise KeyError("outputs meta has no value in module %s" % json.dumps(module))
        group_values = outputs['meta']['value']

        if 'group' not in group_values:
            raise KeyError("outputs meta value has no group in module %s" % json.dumps(module))

        if 'resources' not in module:
            raise KeyError("resources not found in module %s" % json.dumps(module))

        group_name = group_values['group']

        for name, resource in module["resources"].items():
            if not is_vm(name):
                continue

            if group_name not in inventory:
                group_values_without_group_name = dict(group_values)
                del group_values_without_group_name['group']
                inventory[group_name] = {
                    'hosts': [],
                    'vars': group_values_without_group_name,
                    'children': []
                }
                inventory['all']['children'].append(group_name)

            if 'primary' not in resource:
                raise KeyError("resource %s (%s) has not %s" % (name, group_name, 'primary'))

            if 'attributes' not in resource["primary"]:
                raise KeyError("primary of resource %s (%s) has not %s" % (name, group_name, 'attributes'))

            attrs = resource["primary"]["attributes"]

            if 'guest_ip_addresses.0' not in attrs:
                if 'default_ip_address' not in attrs:
                    raise KeyError("resource %s (%s) has not %s and %s attributes" % (name, group_name, 'guest_ip_addresses.0', 'default_ip_address'))

            if 'name' not in attrs:
                raise KeyError("resource %s (%s) has not %s attribute" % (name, group_name, 'name'))

            host=''
            if ('guest_ip_addresses.0' in attrs) and (_is_ip_private(attrs['guest_ip_addresses.0'])):
                host = attrs['guest_ip_addresses.0']
            elif ('guest_ip_addresses.1' in attrs) and (_is_ip_private(attrs['guest_ip_addresses.1'])):
                host = attrs['guest_ip_addresses.1']
            else:
                host = attrs['default_ip_address']

            inventory[group_name]['hosts'].append(host)
            inventory['_meta']['hostvars'][host] = dict()
            inventory['_meta']['hostvars'][host]['hostname'] = attrs['name']
    return inventory

def get_tfstate():
    url = 'http://' + 'consul.service.infra1.consul' + ':8500/v1/kv/' + tf_state_path + '%3A' + project
    r = requests.get(url)
    return json.loads(base64.b64decode(r.json()[0]['Value']), encoding='utf-8')

try:
    tfstate = get_tfstate()
    inventory = _processing(tfstate, _init_inventory())
    sys.stdout.write(json.dumps(inventory, indent=2))
except Exception as e:
    print(str(e), file=sys.stderr)
    print(traceback.format_exc())
    sys.exit(1)
