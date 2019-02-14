#! /usr/bin/env python2
import base64
import os
import sys
import json
from collections import OrderedDict
import requests

vm_prefix = [
    'vsphere_virtual_machine.host'
]

tf_state_path = os.environ['TF_STATE_PATH']
project = os.environ['ANSIBLE_PROJECT']

if tf_state_path == '' or ansible_project == '':
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
        return None

    if len(current_module['outputs']) != 0:
        return current_module['outputs']

    path = current_module['path']
    parent_path = path[:-1]

    parent = None
    for module in modules:
        if module['path'] == parent_path:
            parent = module

    return _get_outputs(parent, modules)


def _processing(tfstate, inventory):
    modules = tfstate["modules"]
    for module in modules:
        if len(module['path']) == 1:
            continue

        outputs = _get_outputs(module, modules)
        group_values = outputs['meta']['value']

        group_name = group_values['group']

        for name, resource in module["resources"].iteritems():
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

            attrs = resource["primary"]["attributes"]

            host = attrs['guest_ip_addresses.0']
            inventory[group_name]['hosts'].append(host)
            inventory['_meta']['hostvars'][host] = dict()
            inventory['_meta']['hostvars'][host]['hostname'] = attrs['name']
    return inventory


def get_tfstate():
    url = 'http://consul.service.infra1.consul:8500/v1/kv/' + tf_state_path + '%3A' + project
    r = requests.get(url)
    return json.loads(base64.b64decode(r.json()[0]['Value']), encoding='utf-8')

try:
    tfstate = get_tfstate()
    inventory = _processing(tfstate, _init_inventory())

    sys.stdout.write(json.dumps(inventory, indent=2))
except Exception as e:
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)
