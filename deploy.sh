#!/bin/bash

sudo apt-get update --fix-missing
sudo apt-get install -y build-essential libssl-dev libpcre3 libpcre3-dev zlib1g-dev libxml2-dev libxslt1-dev libgd-dev libgeoip-dev libluajit-5.1
sudo apt-get install -y python3 python3-dev python3-pip 
sudo apt-get -y purge nginx* nginx-*
sudo apt-get -y autoremove
sudo rm -rf /usr/bin/python && ln -s /usr/bin/python3 /usr/bin/python

sudo mkdir -p /app/lazy_balancer/db
#sudo cp -r /vagrant/* /app/lazy_balancer
sudo chown -R 1000.1000 /app
curl -fsSL https://github.com/openresty/luajit2/archive/v2.1-20231006.tar.gz -o /tmp/luajit.tar.gz 
tar zxf /tmp/luajit.tar.gz -C /tmp && cd /tmp/luajit2-2.1-20231006
make && make install
export LUAJIT_INC=/usr/local/include/luajit-2.1
export LUAJIT_LIB=/usr/local/lib
echo "/usr/local/lib" >> /etc/ld.so.conf
ldconfig
curl -fsSL https://github.com/openresty/lua-resty-core/archive/refs/tags/v0.1.27.tar.gz -o /tmp/lua-resty-core.tar.gz
tar -zxf /tmp/lua-resty-core.tar.gz -C /tmp && cd /tmp/lua-resty-core-0.1.27
make install
curl -fsSL https://github.com/openresty/lua-resty-lrucache/archive/refs/tags/v0.13.tar.gz -o /tmp/lua-resty-lrucache.tar.gz
tar -zxf /tmp/lua-resty-lrucache.tar.gz -C /tmp && cd /tmp/lua-resty-lrucache-0.13
make install
curl -fsSL https://github.com/nicholaschiasson/ngx_upstream_jdomain/archive/refs/tags/1.4.0.tar.gz -o /tmp/ngx_upstream_jdomain.tar.gz
tar -zxf /tmp/ngx_upstream_jdomain.tar.gz -C /tmp
curl -fsSL https://github.com/alibaba/tengine/archive/3.1.0.tar.gz -o /tmp/tengine.tar.gz
tar -zxf /tmp/tengine.tar.gz -C /tmp && cd /tmp/tengine-3.1.0
./configure --user=www-data --group=www-data --prefix=/etc/nginx --sbin-path=/usr/sbin \
      --error-log-path=/var/log/nginx/error.log --conf-path=/etc/nginx/nginx.conf --pid-path=/run/nginx.pid \
      --with-http_secure_link_module \
      --with-http_image_filter_module \
      --with-http_random_index_module \
      --with-threads \
      --with-http_ssl_module \
      --with-http_sub_module \
      --with-http_stub_status_module \
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
      --add-module=./modules/ngx_http_upstream_check_module \
      --add-module=./modules/ngx_http_upstream_session_sticky_module \
      --add-module=./modules/ngx_http_upstream_consistent_hash_module \
      --add-module=./modules/ngx_http_user_agent_module \
      --add-module=./modules/ngx_http_proxy_connect_module \
      --add-module=./modules/ngx_http_concat_module \
      --add-module=./modules/ngx_http_footer_filter_module \
      --add-module=./modules/ngx_http_sysguard_module \
      --add-module=./modules/ngx_http_slice_module \
      --add-module=./modules/ngx_http_lua_module \
      --add-module=./modules/ngx_http_reqstat_module \
      --add-module=/tmp/ngx_upstream_jdomain-1.4.0 \
      --with-http_geoip_module=dynamic \
      --with-stream
make && sudo make install
sudo mkdir -p /etc/nginx/conf.d

cd /app/lazy_balancer
sudo cp -f resource/nginx/nginx.conf.default /etc/nginx/nginx.conf
sudo cp -f resource/nginx/default.* /etc/nginx/ 

sudo pip3 install pip --upgrade
sudo pip3 install -r requirements.txt --upgrade

sudo rm -rf db/*
sudo rm -rf */migrations/00*.py
python manage.py makemigrations --noinput
python manage.py migrate --run-syncdb

sudo sed -i '/^exit 0/i supervisord -c /app/lazy_balancer/service/supervisord.conf' /etc/rc.local
echo "alias supervisoctl='supervisorctl -c /app/lazy_balancer/service/supervisord.conf'" >> ~/.bashrc
sudo supervisord -c /app/lazy_balancer/service/supervisord.conf
