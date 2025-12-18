# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.6.0"

vms = [
    {
        :name => "lazybalancer",
        :eth0 => "192.168.100.100",
        :mem => "2048",
        :cpu => "2"
    },
    #{
    #    :name => "balancer2",
    #    :eth1 => "192.168.100.102",
    #    :mem => "2048",
    #    :cpu => "1"
    #}
]

Vagrant.configure(2) do |config|

  config.vm.box = "cloud-image/ubuntu-20.04"

  vms.each do |opts|
      config.vm.define opts[:name] do |config|
        config.vm.hostname = opts[:name]
          config.vm.provider "virtualbox" do |vb|
            vb.memory = opts[:mem]
            vb.cpus = opts[:cpu]
          end
        config.vm.network :private_network, ip: opts[:eth0]
        config.vm.network :public_network, bridge: "en0: Wi-Fi"

        config.vm.synced_folder ".", "/app/lazy_balancer", type: "nfs", mount_options: ['nolock'], nfs_export: false, nfs_udp: false

      end
  end

  config.vm.provision "shell", privileged: true, path: "deploy.sh"

end
