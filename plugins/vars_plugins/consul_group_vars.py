from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    vars: consul vars by Citius
'''

from ansible.module_utils._text import to_native
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.vars import BaseVarsPlugin
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars
import requests
import base64
import yaml
CACHE = {}
PROJECT = {}

class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities):
        data = {}
        common_data = {}
        common_group_data = {}
        project_common_data = {}
        group_data = {}
        result = {}
        project = ''

        def kv_get(url):
#            print('getting url:', url)
            if url in CACHE:
#                print('getting CACHED url:', url)
                return CACHE[url]
            try:
                r = requests.get(url)
                # print(r)
                if r.status_code == 404:
                    return result
                parsed = r.json()
                if not isinstance(parsed, list):
                    raise ValueError('Incorrect json: ' + r.content)
                def build_tree(branch, v, parts):
                    # print(parts)
                    if len(key_parts)==0:
                        return
                    key = parts.pop(0)
                    if key not in result:
                        if len(parts) == 0:
                            branch[key] = v
                        else:
                            if key not in branch:
                                branch[key] = dict()
                            build_tree(branch[key], v, parts)
                    else:
                        build_tree(branch[key], v, parts)
                for item in parsed:
                    fullkey = item['Key']
                    if not fullkey.startswith(_path):
                        continue
                    no_prefix_key = fullkey[len(_path):]
                    key_parts = [p for p in no_prefix_key.split('/') if p]
                    value = base64.b64decode(item['Value']).decode("utf-8") if item['Value'] else None
                    # print('result: ', result, 'value: ', value, 'key_parts: ', key_parts)
                    build_tree(result, value, key_parts)
            except BaseException as e:
                raise AnsibleError('Error getting vars: %s' % to_native(e))
            CACHE[url] = result
            return result

        for entity in entities:
            if entity.name == 'all':
                # print('group name is', entity.name )
                # print('entity dict is', entity.__dict__ )
                # print('group vars is', entity.vars )
                _path = 'inventory-json/common'
                url = 'http://consul.service.infra1.consul:8500/v1/kv/'+_path+'?recurse'
                common_data=kv_get(url)
                # print('common data:', common_data)
                data=combine_vars(common_data, entity.vars)
                if entity.vars['project']:
                    if project in PROJECT:
                        project = PROJECT[project]
                    else:
                        PROJECT[project]=entity.vars['project']

            elif isinstance(entity, Group):
                print('group name is', entity.name )
                print('entity dict is', entity.__dict__ )
                print('group vars is', entity.vars )
                _path = 'inventory-json/' + entity.name
                url = 'http://consul.service.infra1.consul:8500/v1/kv/'+_path+'?recurse'
                common_group_data=kv_get(url)
                # print('common group data:', common_group_data)

                _path = 'inventory-json/' + PROJECT[project] + '/common'
                url = 'http://consul.service.infra1.consul:8500/v1/kv/'+_path+'?recurse'
                project_common_data=kv_get(url)
                # print('common project data:', project_common_data)

                _path = 'inventory-json/' + PROJECT[project] + '/' + entity.name
                url = 'http://consul.service.infra1.consul:8500/v1/kv/'+_path+'?recurse'
                group_data=kv_get(url)
                # print('project group data:', group_data)

                data=common_group_data
                data=combine_vars(data, project_common_data)
                data=combine_vars(data, group_data)

            elif isinstance(entity, Host):
                # print('host', entity.name)
                pass
            else:
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

        # print(data)
        return data
