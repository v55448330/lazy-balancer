# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.6.0"

vms = [
    {
        :name => "balancer1",
        :eth1 => "192.168.100.101",
        :mem => "2048",
        :cpu => "1"
    },
    {
        :name => "balancer2",
        :eth1 => "192.168.100.102",
        :mem => "2048",
        :cpu => "1"
    }
]

Vagrant.configure(2) do |config|

  config.vm.box = "generic/ubuntu1804"

  vms.each do |opts|
      config.vm.define opts[:name] do |config|
        config.vm.hostname = opts[:name]
          config.vm.provider "virtualbox" do |vb|
            vb.memory = opts[:mem]
            vb.cpus = opts[:cpu]
          end
        config.vm.network :private_network, ip: opts[:eth1]
        config.vm.synced_folder ".", "/app/lazy_balancer"

      end
  end

  config.vm.provision "shell", privileged: true, path: "deploy.sh"

end
