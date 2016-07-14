from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse
from main.models import main_config 
from nginx.views import *
import json
import uuid
import time
import os
 
def view(request):
    _main_config = main_config.objects.all()
    if len(_main_config) != 0:
        _main_config = _main_config[0]

    return render_to_response('main/view.html',{ 'main_config' : _main_config })
    pass

def save(request):
    content = "" 
    try:
        _post = json.loads(request.body)

        print _post

        if _post.has_key('auto_worker_processes'):
            worker_processes = "0"
        else:
            worker_processes = _post.get('worker_processes').replace('_','')

        worker_connections = _post.get('worker_connections').replace('_','')
        keepalive_timeout = _post.get('keepalive_timeout').replace('_','')
        client_max_body_size = _post.get('client_max_body_size').replace('_','')
        access_log = _post.get('access_log')
        error_log = _post.get('error_log')

        if worker_processes and worker_connections and keepalive_timeout and client_max_body_size:
            _config_id = str(uuid.uuid1())
            _config_path= "/etc/nginx/nginx.conf"
            
            if not access_log:
                access_log = "/var/log/nginx/access.log"

            if not error_log:
                error_log = "/var/log/nginx/error.log"

            _main_config = {
                'config_id' : _config_id,
                'worker_processes' : int(worker_processes),
                'worker_connections' : int(worker_connections),
                'keepalive_timeout' : int(keepalive_timeout),
                'client_max_body_size' : int(client_max_body_size),
                'access_log' : access_log,
                'error_log' : error_log,
                'update_time' : time.time()
            }
            print _main_config
            _config_content = build_main_config(_main_config)
            write_config(_config_path,_config_content)

            _test_ret = test_config()
            if _test_ret['status'] == 0:
                write_config(_config_path,_config_content)
                main_config.objects.all().delete()
                main_config.objects.create(**_main_config)
                content = "Success" 
            else:
                content = _test_ret['output']

            reload_config()
        else:
            content = "ArgsError"
    except Exception, e:
        content = str(e)

    return HttpResponse(content)
    pass
#
