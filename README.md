# Vagrant OpenStack Newton

Deploys a single node instance of OpenStack Newton on Ubuntu 16.04.
The initial release only has support for Parallels.  Support for libvirt and
virtualbox will be added later.

## Installation

Make sure you have Ansible version 2.1.x or later installed.  The recommended approach
is to create a virtualenv and install Ansible into that.

```
virtualenv venv
. venv/bin/activate
pip install ansible
```

You also need the vagrant-hostmanager plugin.

```
vagrant plugin install vagrant-hostmanager
```

If you are behind a proxy then ensure your http_proxy and https_proxy
environment variables are set, then ensure that the vagrant-proxyconf plugin
is installed.

```
export http_proxy=http://....
export https_proxy=http://....
vagrant plugin install vagrant-proxyconf

Finally run vagrant to start the installation:

```
vagrant up
```
