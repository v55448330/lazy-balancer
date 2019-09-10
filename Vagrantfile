# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.define "balancer1" do |balancer1|
    config.vm.box = "https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-vagrant.box"
    config.vm.network "forwarded_port", guest: 8000, host: 8000
    config.vm.network "forwarded_port", guest: 80, host: 80
    config.vm.network "forwarded_port", guest: 443, host: 443
    config.vm.network "private_network", ip: "1.1.1.100"
    # config.vm.synced_folder "./", "/app/lazy_balancer"
    config.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.cpus = "1"
    end
    config.vm.provision "shell", inline: <<-SHELL
      sudo apt-get update --fix-missing
      sudo apt-get install -y build-essential libssl-dev libpcre3 libpcre3-dev zlib1g-dev
      sudo apt-get install -y supervisor python-dev python-pip 
      sudo apt-get -y purge nginx* nginx-*
      sudo apt-get -y autoremove

      sudo mkdir -p /app/lazy_balancer/db
      sudo cd /tmp
      cp -r /vagrant/* /app/lazy_balancer
      curl -fsSL https://github.com/alibaba/tengine/archive/2.3.2.tar.gz -o tengine.tar.gz
      tar -zxf tengine.tar.gz && cd tengine-2.3.2
      ./configure --user=www-data --group=www-data --prefix=/etc/nginx --sbin-path=/usr/sbin --error-log-path=/var/log/nginx/error.log --conf-path=/etc/nginx/nginx.conf --pid-path=/run/nginx.pid
      make && sudo make install
      sudo mkdir -p /etc/nginx/conf.d
      echo "daemon off;" | sudo tee -a /etc/nginx/nginx.conf

      cd /app/lazy_balancer
      sudo systemctl enable supervisor
      sudo cp -rf service/* /etc/supervisor/
      sudo rm -rf /etc/supervisor/conf.d/supervisor_balancer_docker.conf

      sudo pip install pip --upgrade
      sudo pip install -r requirements.txt --upgrade

      sudo rm -rf db/*
      sudo rm -rf */migrations
      python manage.py makemigrations --noinput
      python manage.py migrate
      sudo systemctl start supervisor 
    SHELL
  end
end