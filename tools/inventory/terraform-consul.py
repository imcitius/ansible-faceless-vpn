#! /usr/bin/env python2
import base64
import os
import sys
import json

import requests

vm_prefix = [
    'vsphere_virtual_machine.host'
]

project = os.environ['ANSIBLE_PROJECT']


def _init_inventory():
    return {
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
    }


def is_vm(name):
    for pref in vm_prefix:
        if name.startswith(pref):
            return True
    return False


def _processing(tfstate, inventory):
    for module in tfstate["modules"]:
        for name, resource in module["resources"].iteritems():
            if not is_vm(name):
                continue
            attrs = resource["primary"]["attributes"]

            group_name = '-'.join(attrs['name'].split('-')[:-1])

            if group_name not in inventory:
                inventory[group_name] = {
                    'hosts': []
                }
                inventory['all']['children'].append(group_name)

            host = attrs['guest_ip_addresses.0']
            inventory[group_name]['hosts'].append(host)
            inventory['_meta']['hostvars'][host] = dict()
            inventory['_meta']['hostvars'][host]['name'] = attrs['name']

    return inventory


def get_tfstate():
    url = 'http://consul.service.infra1.consul:8500/v1/kv/tf/states/cluster-env%3A' + project
    r = requests.get(url)
    return json.loads(base64.b64decode(r.json()[0]['Value']), encoding='utf-8')


try:
    tfstate = get_tfstate()
    inventory = _processing(tfstate, _init_inventory())
    sys.stdout.write(json.dumps(inventory, indent=2))
except Exception as e:
    sys.stderr.write(str(e)+'\n')
    sys.exit(1)
