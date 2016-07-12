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
    print request.POST

    content = "" 

    if request.POST.has_key('auto_worker_processes'):
        worker_processes = "0"
    else:
        worker_processes = request.POST.get('worker_processes')

    worker_connections = request.POST.get('worker_connections')
    keepalive_timeout = request.POST.get('keepalive_timeout')
    client_max_body_size = request.POST.get('client_max_body_size')
    access_log = request.POST.get('access_log')
    error_log = request.POST.get('error_log')

    if worker_processes and worker_connections and keepalive_timeout and client_max_body_size:
        try:
            _config_id = str(uuid.uuid1())
            _config_test_path = "/tmp/nginx_%s.conf" % _config_id
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
            write_config(_config_test_path,_config_content)

            _test_ret = test_config(_config_test_path)
            if _test_ret['status'] == 0:
                os.remove(_config_test_path)
                write_config(_config_path,_config_content)
                main_config.objects.all().delete()
                _c = main_config(**_main_config)
                _c.save()

                _reload_ret = reload_config()
                if _reload_ret['status'] == 0:
                    content = "Success" 
                else:
                    content = _reload_ret['output']
            else:
                content = _test_ret['output']

        except Exception, e:
            content = str(e)
    else:
        content = "ArgsError"

    #conf_content = build_main_config()
    #write_config("/home/ubuntu/nginx.conf",conf_content)
    return HttpResponse(content)
    pass
#
