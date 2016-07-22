from jinja2 import Environment, FileSystemLoader
from subprocess import check_output, CalledProcessError
from multiprocessing import cpu_count
from django.conf import settings
from proxy.models import proxy_config,upstream_config
from main.models import main_config
import commands
import platform
import json
import os
import psutil

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
        if _p.protocols:
            write_config(_p.ssl_cert_path,_p.ssl_cert)
            write_config(_p.ssl_key_path,_p.ssl_key)
        pass
        write_config(_config_proxy_path,build_proxy_config(_proxy_config))

    return run_shell('nginx -s reload')

def get_statusinfo():
    _phymem = psutil.virtual_memory()
    _disk = psutil.disk_usage('/')
    _conns = psutil.net_connections()
    _nginx_status = False

    try:
        _nginx_status = bool(len(map(int, check_output(["pidof", "nginx"]).split())))
    except CalledProcessError:
        _nginx_status = False
 
    _conn_ESTABLISHED = 0
    _conn_CLOSE_WAIT = 0
    _conn_LISTEN = 0
    _conn_TIME_WAIT = 0
    _conn_FIN_WAIT1 = 0
    _conn_FIN_WAIT2 = 0
    _conn_NONE = 0

    for _conn in _conns:
        if _conn.status is 'ESTABLISHED':
            _conn_ESTABLISHED += 1        
        if _conn.status is 'CLOSE_WAIT':
            _conn_CLOSE_WAIT += 1        
        if _conn.status is 'LISTEN':
            _conn_LISTEN += 1        
        if _conn.status is 'TIME_WAIT':
            _conn_TIME_WAIT += 1        
        if _conn.status is 'FIN_WAIT1':
            _conn_FIN_WAIT1 += 1        
        if _conn.status is 'FIN_WAIT2':
            _conn_FIN_WAIT2 += 1        

    _statusinfo = {
        'cpu_percent' : psutil.cpu_percent(),
        'mem_info' : {
            'available' : _phymem.available/1024/1024,
            'used' : _phymem.used/1024/1024, 
            'total' : _phymem.total/1024/1024 
        },
        'disk_info' : {
            'total' : round(_disk.total/1024.0/1024.0/1024.0,2),
            'used' : round(_disk.used/1024.0/1024.0/1024.0,2),
        },
        'connect_info' : {
            'total' : len(_conns),
            'established' : _conn_ESTABLISHED,
            'listen' : _conn_LISTEN,
            'time_wait' : _conn_TIME_WAIT,
            'close_wait' : _conn_CLOSE_WAIT,
            'fin_wait' : _conn_FIN_WAIT1 + _conn_FIN_WAIT2,
            'none' : len(_conns) - _conn_ESTABLISHED - _conn_LISTEN -_conn_TIME_WAIT - _conn_CLOSE_WAIT - _conn_FIN_WAIT1 - _conn_FIN_WAIT2
        },
        'nginx_status' : _nginx_status
    }

    return _statusinfo


def get_sysinfo():
    _disk_info = psutil.disk_usage('/')
    _nic_info = []
    for nic,addrs in psutil.net_if_addrs().items():
        if ":" not in addrs[0].address:
            _nic_info.append({'nic':nic,'address':addrs[0].address})
    _sysinfo = {
        'nic' : _nic_info,
        'platform' : {
            'node' : platform.node(),
            'system' : platform.system(),
            'release' : platform.release(),
            'processor' : platform.processor()
        },
        'nginx' : run_shell('nginx -v')['output'].split(': ')[1]
    }
    return _sysinfo
