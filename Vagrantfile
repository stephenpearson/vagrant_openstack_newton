# -*- mode: ruby -*-
# vi: set ft=ruby :

# Copyright 2016 Stephen Pearson <stephen@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

Vagrant.configure(2) do |config|
  if Vagrant.has_plugin?("vagrant-proxyconf")
    config.proxy.http     = ENV['http_proxy']
    config.proxy.https    = ENV['https_proxy']

    PROXY_IGNORE=%w(newton controller newton.local.xyz controller.local.xyz localhost 127.0.0.1 127.0.1.1)
    config.proxy.no_proxy = "#{ENV['no_proxy']},#{PROXY_IGNORE.join(',')}"
  end

  config.vm.box_check_update = true
  config.vm.network "private_network", ip: "192.168.99.3",
                     auto_config: false

  config.vm.provider :libvirt do |vm, override|
    override.vm.box = "stephenpearson/ubuntu-16.04"
    vm.driver = "kvm"
    vm.memory = 4096
    vm.cpus = 2
    vm.nested = true
    vm.storage_pool_name = "ssd"

    # Cinder storage
    vm.storage :file, :size => "50G"
  end

  config.vm.provider :parallels do |vm, override|
    override.vm.box = "parallels/ubuntu-16.04"
    vm.name = "newton"
    vm.check_guest_tools = false
    vm.memory = 4096
    vm.cpus = 2
    vm.customize ["set", :id, "--nested-virt", "on"]

    # Cinder storage
    vm.customize ['set', :id, '--device-add', 'hdd', '--size', '51200']
  end

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "provisioning/site.yml"
  end
end
