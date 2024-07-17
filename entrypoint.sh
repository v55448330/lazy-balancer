#!/bin/ash

WORKDIR=/app/lazy_balancer

cd ${WORKDIR}

if [ ! -e "db/db.sqlite3" ]; then
    mkdir -p ${WORKDIR}/db
    cp -v ${WORKDIR}/db.sqlite3.init ${WORKDIR}/db/db.sqlite3
fi

supervisord -c "/app/lazy_balancer/service/supervisord_docker.conf"