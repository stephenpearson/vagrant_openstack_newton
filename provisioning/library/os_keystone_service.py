#!/usr/bin/python
# Copyright 2016 Sam Yaple
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

def _debug(name, obj):
    with open("/tmp/debug-%s" % name, "w") as f:
        f.write(str(obj) + "\n")

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion

DOCUMENTATION = '''
---
module: os_keystone_service
short_description: Manage OpenStack Identity services
extends_documentation_fragment: openstack
author: "Sam Yaple (@SamYaple)"
version_added: "2.2"
description:
    - Create, update, or delete OpenStack Identity service. If a service
      with the supplied name already exists, it will be updated with the
      new description and enabled attributes.
options:
   name:
     description:
        - Name of the service
     required: true
   description:
     description:
        - Description of the service
     required: false
     default: None
   enabled:
     description:
        - Is the service enabled
     required: false
     default: True
   service_type:
     description:
        - The type of service
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a service for glance
- os_keystone_service:
     cloud: mycloud
     state: present
     name: glance
     service_type: image
     description: OpenStack Image Service
# Delete a service
- os_keystone_service:
     cloud: mycloud
     state: absent
     name: glance
     service_type: image
'''

RETURN = '''
service:
    description: Dictionary describing the service.
    returned: On success when I(state) is 'present'
    type: dictionary
    contains:
        id:
            description: Service ID.
            type: string
            sample: "3292f020780b4d5baf27ff7e1d224c44"
        name:
            description: Service name.
            type: string
            sample: "glance"
        service_type:
            description: Service type.
            type: string
            sample: "image"
        description:
            description: Service description.
            type: string
            sample: "OpenStack Image Service"
        enabled:
            description: Service status.
            type: boolean
            sample: True
id:
    description: The service ID.
    returned: On success when I(state) is 'present'
    type: string
    sample: "3292f020780b4d5baf27ff7e1d224c44"
'''


def _needs_update(module, service):
    if service.enabled != module.params['enabled']:
        return True
    if service.description is not None and \
       service.description != module.params['description']:
        return True
    return False


def _system_state_change(module, service):
    state = module.params['state']
    if state == 'absent' and service:
        return True

    if state == 'present':
        if service is None:
            return True
        return _needs_update(module, service)

    return False

def _is_v2(cloud):
    return cloud.cloud_config.get_api_version('identity').startswith('2')

def _mk_service_tuples(module):
    result = {}
    region = module.params['region']
    enabled = module.params['enabled']

    public_endpoint = module.params['public_endpoint']
    admin_endpoint = module.params['admin_endpoint']
    internal_endpoint = module.params['internal_endpoint']

    if public_endpoint:
        result[(region, 'public')] = (public_endpoint, enabled)
    if admin_endpoint:
        result[(region, 'admin')] = (admin_endpoint, enabled)
    if internal_endpoint:
        result[(region, 'internal')] = (internal_endpoint, enabled)

    return result

def _service_to_tuple(service):
    return((service['region'], service['interface']))

def _get_service_ids(endpoints, ep):
    return [e['id'] for e in endpoints if ep['region'] == e['region'] and
                                       ep['interface'] == e['interface']]

def _conv_v2_ep_to_v3(endpoints):
    result = list()
    for ep in endpoints:
        for iface in ('public', 'internal', 'admin'):
            entry = dict()
            try:
                url = ep["%surl" % iface]
            except KeyError:
                url = None
            if url:
                entry['id'] = ep['id']
                entry['region'] = ep['region']
                entry['url'] = url
                entry['enabled'] = ep['enabled']
                entry['interface'] = iface
                entry['service_id'] = ep['service_id']
                result.append(entry)
    return result

def _get_endpoints(cloud, service):
    all_ep = cloud.list_endpoints()
    endpoints = [e for e in all_ep if e['service_id'] == service['id']]
    if _is_v2(cloud):
        endpoints = _conv_v2_ep_to_v3(endpoints)
    current = {_service_to_tuple(e):
              (e['url'], e['enabled'], _get_service_ids(endpoints, e))
              for e in endpoints}
    return (endpoints, current)

def _update_endpoints(cloud, module, service):
    (endpoints, current) = _get_endpoints(cloud, service)
    requested = _mk_service_tuples(module)

    add_ep = set(requested.keys()) - set(current.keys())
    del_ep = set(current.keys()) - set(requested.keys())
    mod_ep = set(current.keys()).intersection(set(requested.keys()))
    mod_ep = [ep for ep in mod_ep if current[ep][0] != requested[ep][0] or
                                     current[ep][1] != requested[ep][1]]

    _debug("add_ep", add_ep)
    _debug("del_ep", del_ep)
    _debug("mod_ep", mod_ep)
    _debug("requested", requested)

    changed = _del_duplicate_endpoints(cloud, current)
    _debug("1", changed)
    changed = _del_endpoints(cloud, del_ep, current) | changed
    _debug("2", changed)
    changed = _del_endpoints(cloud, mod_ep, current) | changed
    _debug("3", changed)
    changed = _add_endpoints(cloud, add_ep, requested, service, module) | changed
    _debug("4", changed)
    changed = _add_endpoints(cloud, mod_ep, requested, service, module) | changed
    _debug("5", changed)
    (endpoints, current) = _get_endpoints(cloud, service)
    changed = _del_duplicate_endpoints(cloud, current) | changed
    _debug("6", changed)

    return changed

def _del_duplicate_endpoints(cloud, endpoints):
    changed = False
    for ep in endpoints:
        for dupe in endpoints[ep][2][1:]:
            cloud.delete_endpoint(dupe)
            changed = True
    return changed

def _del_endpoints(cloud, del_ep, current):
    changed = False
    for ep in del_ep:
        service_id = current[ep][2][0]
        cloud.delete_endpoint(service_id)
        changed = True
    return changed

def _extract_endpoint(requested, add_ep, ep_type):
    key = filter(lambda x: x[1] == ep_type, add_ep)
    if key:
        try:
            endpoint_tuple = requested[key[0]]
        except KeyError:
            return None
        if endpoint_tuple[1] == None:
            return None
        else:
            return endpoint_tuple[0]
    else:
        return None

def _add_endpoints(cloud, add_ep, requested, service, module):
    region = module.params['region']
    public_endpoint = _extract_endpoint(requested, add_ep, 'public')
    internal_endpoint = _extract_endpoint(requested, add_ep, 'internal')
    admin_endpoint = _extract_endpoint(requested, add_ep, 'admin')
    cloud.create_endpoint(service, public_url=public_endpoint,
                          internal_url=internal_endpoint,
                          admin_url=admin_endpoint, region=region)

    return (bool(public_endpoint) |
            bool(internal_endpoint) |
            bool(admin_endpoint))

def main():
    argument_spec = openstack_full_argument_spec(
        description=dict(default=None),
        enabled=dict(default=True, type='bool'),
        name=dict(required=True),
        service_type=dict(required=True),
        public_endpoint=dict(default=None),
        admin_endpoint=dict(default=None),
        internal_endpoint=dict(default=None),
        region=dict(default=None),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    if StrictVersion(shade.__version__) < StrictVersion('1.6.0'):
        module.fail_json(msg="To utilize this module, the installed version of"
                             "the shade library MUST be >=1.6.0")

    description = module.params['description']
    enabled = module.params['enabled']
    name = module.params['name']
    state = module.params['state']
    service_type = module.params['service_type']
    public_endpoint = module.params['public_endpoint']
    admin_endpoint = module.params['admin_endpoint']
    internal_endpoint = module.params['internal_endpoint']
    region = module.params['region']

    try:
        cloud = shade.operator_cloud(**module.params)

        services = cloud.search_services(name_or_id=name,
                                         filters=dict(type=service_type))

        if len(services) > 1:
            module.fail_json(msg='Service name %s and type %s are not unique' %
                (name, service_type))
        elif len(services) == 1:
            service = services[0]
        else:
            service = None

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, service))

        if state == 'present':
            if service is None:
                service = cloud.create_service(name=name,
                    description=description, type=service_type, enabled=True)
                changed = True
            else:
                if _needs_update(module, service):
                    service = cloud.update_service(
                        service.id, name=name, type=service_type, enabled=enabled,
                        description=description)
                    changed = True
                else:
                    changed = False
            changed = _update_endpoints(cloud, module, service) | changed
            module.exit_json(changed=changed, service=service, id=service.id)

        elif state == 'absent':
            if service is None:
                changed=False
            else:
                cloud.delete_service(service.id)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
