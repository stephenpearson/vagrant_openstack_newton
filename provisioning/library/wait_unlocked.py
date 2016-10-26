#!/usr/bin/python
# -*- coding: utf-8 -*-

import fcntl

from ansible.module_utils.basic import *


def is_locked(fname):
    try:
        f = open(fname, 'w')
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return False
    except IOError:
        f.close()
        return True

def wait_on_lock(fname, retries, poll):
    if retries is None:
        retries = 1
    if poll is None:
        poll = 2.0
    was_locked = False
    for i in range(retries):
        while is_locked(fname):
            was_locked = True
            time.sleep(poll)
        time.sleep(poll)
    return was_locked

def main():
    fields = {
        "filename": {"required": True, "type": "str"},
        "poll_interval": {"required": False, "type": "float"},
        "retries": {"required": False, "type": "int"}
    }
    module = AnsibleModule(argument_spec=fields)
    result = wait_on_lock(module.params['filename'],
                          module.params['retries'],
                          module.params['poll_interval'])
    module.exit_json(changed=result, meta={})

if __name__ == "__main__":
    main()
