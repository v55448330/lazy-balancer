from jinja2 import Environment, FileSystemLoader
from multiprocessing import cpu_count
from django.conf import settings

def build_main_config(_config):
    env = Environment(
        loader=FileSystemLoader(
            settings.NGINX_TEMPLATES
        )
    )
    template = env.get_template('nginx.template')
    _cpu_count = 1

    if _config['worker_processes'] == 0:
        _cpu_count = cpu_count()
    else:
        _cpu_count = _config['worker_processes']

    nginx_main_config = {
        "config_id" : _config['config_id'],
        "worker_processes" : cpu_count(),
        "worker_connections" : _config['worker_connections'],
        "keepalive_timeout" : _config['keepalive_timeout'],
        "client_max_body_size" : _config['client_max_body_size'],
        "access_log" : _config['access_log'],
        "error_log" : _config['error_log'],
    }
    print nginx_main_config

    return template.render(nginx_main_config)

def write_config(conf_path,conf_content):
    f = open(conf_path, 'w')
    f.write(conf_content)
    f.close()
