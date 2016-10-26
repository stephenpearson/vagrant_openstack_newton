#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from ansible.module_utils.basic import *


def set_iface_state(interface, new_state):
    with open("/sys/class/net/%s/operstate" % interface, "r") as f:
        lines = f.readlines()
        cur_state = lines[0].strip()
    if(cur_state == "down" and new_state == "up"):
        os.system("/sbin/ifup %s" % interface)
        return True
    if(cur_state == "up" and new_state == "down"):
        os.system("/sbin/ifdown %s" % interface)
        return True
    return False

def main():
    fields = {
        "interface": {"required": True, "type": "str"},
        "state": {"required": True, "type": "str"}
    }
    module = AnsibleModule(argument_spec=fields)
    result = set_iface_state(module.params['interface'],
                             module.params['state'])
    module.exit_json(changed=result, meta={})

if __name__ == "__main__":
    main()
