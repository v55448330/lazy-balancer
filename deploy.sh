#!/bin/bash

TENGINE_VERSION=3.1.0
tempDir="$(mktemp -d)" && cd ${tempDir} 

sudo apt-get update --fix-missing
sudo apt-get install -y build-essential libssl-dev libpcre3 libpcre3-dev zlib1g-dev libxml2-dev libxslt1-dev libgd-dev libgeoip-dev libjemalloc-dev
sudo apt-get install -y python3 python3-dev python3-pip
sudo apt-get -y purge nginx* nginx-*
sudo apt-get -y autoremove
sudo rm -rf /usr/bin/python && ln -s /usr/bin/python3 /usr/bin/python

sudo mkdir -p /app/lazy_balancer/db
#sudo cp -r /vagrant/* /app/lazy_balancer
sudo chown -R 1000.1000 /app

curl -fsSL https://github.com/alibaba/tengine/archive/${TENGINE_VERSION}.tar.gz -o /tmp/tengine.tar.gz 
git clone https://github.com/zhouchangxun/ngx_healthcheck_module.git ${tempDir}/ngx_healthcheck_module 
git clone https://github.com/vozlt/nginx-module-vts.git ${tempDir}/nginx-module-vts 
git clone https://github.com/vozlt/nginx-module-sts.git ${tempDir}/nginx-module-sts 
git clone https://github.com/vozlt/nginx-module-stream-sts.git ${tempDir}/nginx-module-stream-sts 
tar -zxf /tmp/tengine.tar.gz -C /tmp && cd /tmp/tengine-${TENGINE_VERSION} 
patch -p1 < ${tempDir}/ngx_healthcheck_module/nginx_healthcheck_for_tengine_2.3+.patch 
./configure --user=www-data --group=www-data \
      --prefix=/etc/nginx --sbin-path=/usr/sbin \
      --error-log-path=/var/log/nginx/error.log \
      --conf-path=/etc/nginx/nginx.conf --pid-path=/run/nginx.pid \
      --with-http_secure_link_module \
      --with-http_image_filter_module \
      --with-http_random_index_module \
      --with-threads \
      --with-http_ssl_module \
      --with-http_sub_module \
      --with-http_gunzip_module \
      --with-http_gzip_static_module \
      --with-http_realip_module \
      --with-compat \
      --with-file-aio \
      --with-http_dav_module \
      --with-http_degradation_module \
      --with-http_flv_module \
      --with-http_mp4_module \
      --with-http_xslt_module \
      --with-http_auth_request_module \
      --with-http_addition_module \
      --with-http_v2_module \
      --with-http_geoip_module \
      --with-stream_geoip_module \
      --with-stream \
      --with-jemalloc \
      --add-module=./modules/ngx_http_upstream_vnswrr_module \
      --add-module=./modules/ngx_http_upstream_dynamic_module \
      --add-module=./modules/ngx_http_upstream_consistent_hash_module \
      --add-module=${tempDir}/nginx-module-vts \
      --add-module=${tempDir}/nginx-module-sts \
      --add-module=${tempDir}/nginx-module-stream-sts \
      --add-module=${tempDir}/ngx_healthcheck_module 

make && sudo make install
sudo mkdir -p /etc/nginx/conf.d

cd /app/lazy_balancer
sudo cp -f resource/nginx/nginx.conf.default /etc/nginx/nginx.conf
sudo cp -f resource/nginx/default.* /etc/nginx/ 

sudo pip3 install pip --upgrade
sudo pip3 install -r requirements.txt --upgrade

sudo mkdir -p db
sudo cp -v db.sqlite3.init db/db.sqlite3
sudo rm -rf */migrations/00*.py

#sudo sed -i '/^exit 0/i supervisord -c /app/lazy_balancer/service/supervisord.conf' /etc/rc.local
echo "alias supervisorctl='supervisorctl -c /app/lazy_balancer/service/supervisord.conf'" >> ~/.bashrc
sudo supervisord -c /app/lazy_balancer/service/supervisord.conf
