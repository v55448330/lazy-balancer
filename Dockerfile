FROM python:3.9-alpine

ENV TENGINE_VERSION 3.1.0
ENV LAZYBALANCER_VERSION v1.4.0beta

COPY . /app/lazy_balancer

RUN set -x \
    #&& addgroup -g 101 -S www-data \
    && adduser -S -D -H -u 82 -h /var/cache/nginx -s /sbin/nologin -G www-data -g www-data www-data \
    && apkArch="$(cat /etc/apk/arch)" \
    && tempDir="$(mktemp -d)" && cd ${tempDir} \
    && chown nobody:nobody ${tempDir} \
    && apk add --no-cache --virtual .build-deps curl \
                git \
                tzdata \
                gcc \
                libc-dev \
                musl-dev \
                build-base \
                make \
                cargo \
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
                python3-dev \
                libffi-dev \
                libgcc \
                jemalloc-dev \
                libgd \
                libxslt \
                libxml2 \
                pcre \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && python3 -m pip install --upgrade pip \
    && curl -fsSL https://github.com/alibaba/tengine/archive/${TENGINE_VERSION}.tar.gz -o /tmp/tengine.tar.gz \
    && git clone https://github.com/zhouchangxun/ngx_healthcheck_module.git ${tempDir}/ngx_healthcheck_module \
    && git clone https://github.com/vozlt/nginx-module-vts.git ${tempDir}/nginx-module-vts \
    && git clone https://github.com/vozlt/nginx-module-sts.git ${tempDir}/nginx-module-sts \
    && git clone https://github.com/vozlt/nginx-module-stream-sts.git ${tempDir}/nginx-module-stream-sts \
    && tar -zxf /tmp/tengine.tar.gz -C /tmp && cd /tmp/tengine-${TENGINE_VERSION} \
    && patch -p1 < ${tempDir}/ngx_healthcheck_module/nginx_healthcheck_for_tengine_2.3+.patch \
    && ./configure --user=www-data --group=www-data \
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
            --add-module=${tempDir}/ngx_healthcheck_module \
    && make && make install \
    && cd /app/lazy_balancer \
    && mkdir -p /etc/nginx/conf.d \
    && cp -f resource/nginx/nginx.conf.default /etc/nginx/nginx.conf \
    && cp -f resource/nginx/default.* /etc/nginx/ \
    && rm -rf */migrations/00*.py \
    && rm -rf env \
    && pip3 --no-cache-dir install -r requirements.txt \
    && runDeps="$( \
        scanelf --needed --nobanner /usr/sbin/nginx \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u \
    )" \
    && apk add --no-cache --virtual .nginx-rundeps ${runDeps} \
    && apk add --no-cache gettext \
    && apk del .build-deps \
    && rm -rf ${tempDir} \
    && rm -rf /usr/local/lib/python3.9/config-3.9-x86_64-linux-gnu/ \
    && chown -R www-data:www-data /app \
    && echo -e '#!/bin/ash\nsupervisorctl -c /app/lazy_balancer/service/supervisord.conf' > /usr/bin/sc \
    && chmod +x /usr/bin/sc

WORKDIR /app/lazy_balancer 

EXPOSE 8000

CMD [ "/bin/ash", "-c", "/app/lazy_balancer/entrypoint.sh" ]
