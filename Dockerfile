FROM alpine:3.10

ENV TENGINE_VERSION 2.3.2
ENV LAZYBALANCER_VERSION v0.8.1beta

RUN set -x \
    && addgroup -g 101 -S www-data \
    && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G www-data -g www-data www-data \
    && apkArch="$(cat /etc/apk/arch)" \
    && tempDir="$(mktemp -d)" \
    && chown nobody:nobody ${tempDir} \
    && apk add --no-cache python2 py2-pip supervisor pcre \
    && apk add --no-cache --virtual .build-deps \
                gcc \
                libc-dev \
                make \
                openssl-dev \
                pcre-dev \
                zlib-dev \
                linux-headers \
                libxslt-dev \
                gd-dev \
                geoip-dev \
                perl-dev \
                libedit-dev \
                mercurial \
                alpine-sdk \
                findutils \
                python-dev \
    && curl -fsSL https://github.com/alibaba/tengine/archive/${TENGINE_VERSION}.tar.gz -o tengine.tar.gz \
    && tar zxf tengine.tar.gz -C ${tempDir} \
    && cd ${tempDir}/tengine-${TENGINE_VERSION} \
    && ./configure --user=www-data --group=www-data \
            --prefix=/etc/nginx --sbin-path=/usr/sbin \
            --error-log-path=/var/log/nginx/error.log \
            --conf-path=/etc/nginx/nginx.conf --pid-path=/run/nginx.pid \
            --ngx_http_lua_module \
            --with-http_reqstat_module \
            --with-http_stub_status_module \
    && make && make install \
    && mkdir -p /etc/nginx/conf.d \
    && echo "daemon off;" | sudo tee -a /etc/nginx/nginx.conf \
    && mkdir -p /app/lazy_balancer \
    && curl -fsSL https://github.com/v55448330/lazy-balancer/archive/${LAZYBALANCER_VERSION}.tar.gz -o lazybalancer.tar.gz \
    && tar zxf lazybalancer.tar.gz --strip-components=1 -C /app/lazy_balancer \
    && chown -R www-data:www-data /app \
    && cd /app/lazy_balancer && mkdir -p /etc/supervisor /var/log/supervisor && cp -rf service/* /etc/supervisor/ \
    && pip install -r requirements.txt \
    && apk del .build-deps \
    && rm -rf ${tempDir}

WORKDIR /app/lazy_balancer 

EXPOSE 8000

CMD [ "supervisord", "-c", "/etc/supervisor/supervisord_docker.conf" ]


