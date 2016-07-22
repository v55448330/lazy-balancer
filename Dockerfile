FROM ubuntu:14.04
MAINTAINER Zhang XiaoBao <crazy.zhang@outlook.com>

RUN apt-get update && apt-get install -y nginx supervisor python-dev python-pip
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

ADD . /app/nginx_balancer
WORKDIR /app/nginx_balancer

RUN pip install pip --upgrade
RUN pip install -r requirements.txt --upgrade

RUN cp -rf service/supervisord_docker.conf /etc/supervisor/supervisord.conf && \
    cp -rf service/conf.d/supervisor_balancer.conf /etc/supervisor/conf.d

RUN python manage.py makemigrations && python manage.py migrate

EXPOSE 80 443 8000

CMD ["/usr/bin/supervisord"]

