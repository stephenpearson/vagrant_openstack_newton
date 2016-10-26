#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import re
from os import listdir

from ansible.module_utils.basic import AnsibleModule

def get_unused_nic(ifpath, netpath):
    with open(ifpath, "r") as f:
        active = set()
        p = re.compile(r"auto\s(.+)$")
        for l in f.readlines():
            l = l.strip()
            m = p.match(l)
            if m:
                active.add(m.group(1))

        netpath = "/sys/class/net"
        alliface = {f for f in listdir(netpath)}

        return sorted(alliface - active)[0]

def main():
    fields = {
        "interfaces_path": { "required": True, "type": "str" },
        "networks_path": { "required": True, "type": "str" }
    }
    module = AnsibleModule(argument_spec=fields)
    result = get_unused_nic(module.params['interfaces_path'],
                            module.params['networks_path'])
    data = { "provider_net_nic": result }
    print(json.dumps({"change": False, "ansible_facts": data}))

if __name__ == "__main__":
    main()
