from jinja2 import Environment, FileSystemLoader
from multiprocessing import cpu_count
from django.conf import settings

def build_main_config():
    env = Environment(
        loader=FileSystemLoader(
            settings.NGINX_TEMPLATES
        )
    )
    template = env.get_template('nginx.template')
    nginx_main_config = {
        "worker_processes" : cpu_count(),
        "worker_connections" : 65535,
        "keepalive_timeout" : 65,
        "client_max_body_size" : "10M",
        "access_log" : "",
        "error_log" : "",
    }
    return template.render(nginx_main_config)

def write_config(conf_path,conf_content):
    f = open(conf_path, 'w')
    f.write(conf_content)
    f.close()
