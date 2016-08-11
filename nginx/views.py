from jinja2 import Environment, FileSystemLoader
from subprocess import check_output, CalledProcessError
from django.conf import settings
from proxy.models import proxy_config,upstream_config
from main.models import main_config
import commands
import platform
import os
import psutil
import requests

def clean_dir(dir_path):
    filelist=[]
    filelist=os.listdir(dir_path)
    for f in filelist:
        filepath = os.path.join(dir_path,f)
        if os.path.isfile(filepath):
            os.remove(filepath)
    return True

def load_template(template):
    env = Environment(
        loader=FileSystemLoader(
            settings.NGINX_TEMPLATES
        )
    )
    return env.get_template(template)

def build_main_config(config):
    template = load_template('nginx.template')

    return template.render(config)

def build_proxy_config(config):
    template = load_template('proxy.template')

    return template.render(config)

def build_default_config(config):
    template = load_template('default.template')

    return template.render(config)

def write_config(conf_path,conf_context):
    f = open(conf_path, 'w')
    f.write(conf_context)
    f.close()

def run_shell(cmd):
    (status,output) = commands.getstatusoutput(cmd)
    context = {
        'status':status,
        'output':output,
    }
    return context

def test_config():
    return run_shell('nginx -t')

def reload_config():
    config_nginx_path = "/etc/nginx/nginx.conf"
    config_default_path = "/etc/nginx/conf.d/default.conf"
    os.remove(config_nginx_path)
    clean_dir("/etc/nginx/conf.d")
    m_config = main_config.objects.all()[0].__dict__
    write_config(config_nginx_path,build_main_config(m_config))

    proxy_port_list = []
    proxy_config_list = proxy_config.objects.filter(status=True)
    for p in proxy_config_list:
        u_list = []
        for u in p.upstream_list.all():
            u_list.append(u.__dict__)
            pass
        p_config = { 'proxy' : p.__dict__ , 'upstream' : u_list }
        config_proxy_path = "/etc/nginx/conf.d/%s.conf" % p.config_id
        if p.protocols:
            write_config(p.ssl_cert_path,p.ssl_cert)
            write_config(p.ssl_key_path,p.ssl_key)
        pass
        proxy_port_list.append(p.listen)
        write_config(config_proxy_path,build_proxy_config(p_config))

    write_config(config_default_path,build_default_config({'listen_list':list(set(proxy_port_list))}))

    return run_shell('nginx -s reload')

def get_sys_status():
    phymem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    conns = psutil.net_connections()
    nginx_status = False

    try:
        nginx_status = bool(len(map(int, check_output(["pidof", "nginx"]).split())))
    except CalledProcessError:
        nginx_status = False

    conn_ESTABLISHED = 0
    conn_CLOSE_WAIT = 0
    conn_LISTEN = 0
    conn_TIME_WAIT = 0
    conn_FIN_WAIT1 = 0
    conn_FIN_WAIT2 = 0
    conn_NONE = 0

    for conn in conns:
        if conn.status is 'ESTABLISHED':
            conn_ESTABLISHED += 1
        if conn.status is 'CLOSE_WAIT':
            conn_CLOSE_WAIT += 1
        if conn.status is 'LISTEN':
            conn_LISTEN += 1
        if conn.status is 'TIME_WAIT':
            conn_TIME_WAIT += 1
        if conn.status is 'FIN_WAIT1':
            conn_FIN_WAIT1 += 1
        if conn.status is 'FIN_WAIT2':
            conn_FIN_WAIT2 += 1

    statusinfo = {
        'cpu_percent' : psutil.cpu_percent(),
        'mem_info' : {
            'available' : phymem.available/1024/1024,
            'used' : (phymem.used-phymem.cached)/1024/1024,
            'total' : phymem.total/1024/1024
        },
        'disk_info' : {
            'total' : round(disk.total/1024.0/1024.0/1024.0,2),
            'used' : round(disk.used/1024.0/1024.0/1024.0,2),
        },
        'connect_info' : {
            'total' : len(conns),
            'established' : conn_ESTABLISHED,
            'listen' : conn_LISTEN,
            'time_wait' : conn_TIME_WAIT,
            'close_wait' : conn_CLOSE_WAIT,
            'fin_wait' : conn_FIN_WAIT1 + conn_FIN_WAIT2,
            'none' : len(conns) - conn_ESTABLISHED - conn_LISTEN - conn_TIME_WAIT - conn_CLOSE_WAIT - conn_FIN_WAIT1 - conn_FIN_WAIT2
        },
        'nginx_status' : nginx_status
    }

    return statusinfo


def get_sys_info():
    disk_info = psutil.disk_usage('/')
    nic_info = []
    for nic,addrs in psutil.net_if_addrs().items():
        if ":" not in addrs[0].address:
            if nic != "lo":
                nic_info.append({'nic':nic,'address':addrs[0].address})
    sysinfo = {
        'nic' : nic_info,
        'platform' : {
            'node' : platform.node(),
            'system' : platform.system(),
            'release' : platform.release(),
            'processor' : platform.processor()
        },
        'nginx' : run_shell('nginx -v')['output'].split(': ')[1]
    }
    return sysinfo

def post_request(url,headers={}):
    resp = requests.get(url,timeout=1,headers=headers)
    return resp

def get_proxy_http_status():
    url = "http://127.0.0.1/up_status?format=json"
    ret = post_request(url).json()
    return ret

def get_req_status():
    url = "http://127.0.0.1/req_status"
    req_status = post_request(url).text
    ret = []
    for req in req_status.split('\n'):
        r = req.split(',')
        if r[0] != "":
            ret.append(r)
    return ret
