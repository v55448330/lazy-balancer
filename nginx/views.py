from jinja2 import Environment, FileSystemLoader
from multiprocessing import cpu_count
from django.conf import settings
from proxy.models import proxy_config,upstream_config
from main.models import main_config
import commands
import json
import os


def clean_dir(_dir_path):
    filelist=[]  
    filelist=os.listdir(_dir_path)  
    for f in filelist:  
        filepath = os.path.join(_dir_path,f)  
        if os.path.isfile(filepath):  
            os.remove(filepath)  
    print _dir_path+" removed!"  
    return True

def load_template(_template):
    env = Environment(
        loader=FileSystemLoader(
            settings.NGINX_TEMPLATES
        )
    )
    return env.get_template(_template)

def build_main_config(_config):
    template = load_template('nginx.template')

    if _config['worker_processes'] == 0:
        _config['worker_processes'] = cpu_count()

    return template.render(_config)

def build_proxy_config(_config):
    template = load_template('proxy.template')

    if not _config['proxy'].has_key('protocols'):
        _config['proxy']['protocols'] = False
        _config['proxy']['ssl_cert'] = None
        _config['proxy']['ssl_key'] = None
 
    return template.render(_config)

def write_config(_conf_path,_conf_content):
    _f = open(_conf_path, 'w')
    _f.write(_conf_content)
    _f.close()

def run_shell(_cmd):
    (_status,_output) = commands.getstatusoutput(_cmd)
    _content = {
        'status':_status,
        'output':_output,
    }
    return _content

def test_config():
    return run_shell('nginx -t')

def reload_config():
    _config_nginx_path = "/etc/nginx/nginx.conf"
    os.remove(_config_nginx_path)
    clean_dir("/etc/nginx/conf.d")
    _main_config = main_config.objects.all()[0].__dict__
    write_config(_config_nginx_path,build_main_config(_main_config))

    _proxy_config_list = proxy_config.objects.filter(status=True)
    for _p in _proxy_config_list:
        _u_list = []
        for _u in _p.upstream_list.all():
            _u_list.append(_u.__dict__)
            pass
        _proxy_config = { 'proxy' : _p.__dict__ , 'upstream' : _u_list }
        _config_proxy_path = "/etc/nginx/conf.d/%s.conf" % _p.config_id
        write_config(_config_proxy_path,build_proxy_config(_proxy_config))
        pass


    return run_shell('nginx -s reload')


