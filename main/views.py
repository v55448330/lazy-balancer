from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from main.models import main_config
from nginx.views import *
import json
import uuid
import time
import os

@login_required(login_url="/login/")
def view(request):
    main_config = main_config.objects.all()
    if len(main_config) != 0:
        main_config = main_config[0]

    user = {
        'name':request.user,
        'date':time.time()
    }

    return render_to_response('main/view.html',{ 'main_config' : main_config, 'user' : user })
    pass

@login_required(login_url="/login/")
def save(request):
    content = ""
    try:
        post = json.loads(request.body)

        print post

        if post.has_key('auto_worker_processes'):
            worker_processes = "0"
        else:
            worker_processes = post.get('worker_processes').replace('_','')

        worker_connections = post.get('worker_connections').replace('_','')
        keepalive_timeout = post.get('keepalive_timeout').replace('_','')
        client_max_body_size = post.get('client_max_body_size').replace('_','')
        access_log = post.get('access_log')
        error_log = post.get('error_log')

        if worker_processes and worker_connections and keepalive_timeout and client_max_body_size:
            config_id = str(uuid.uuid1())
            config_path= "/etc/nginx/nginx.conf"

            if not access_log:
                access_log = "/var/log/nginx/access.log"

            if not error_log:
                error_log = "/var/log/nginx/error.log"

            main_config = {
                'config_id' : config_id,
                'worker_processes' : int(worker_processes),
                'worker_connections' : int(worker_connections),
                'keepalive_timeout' : int(keepalive_timeout),
                'client_max_body_size' : int(client_max_body_size),
                'access_log' : access_log,
                'error_log' : error_log,
                'update_time' : time.time()
            }
            print main_config
            config_content = build_main_config(main_config)
            write_config(config_path,_config_content)

            test_ret = test_config()
            if test_ret['status'] == 0:
                write_config(config_path,_config_content)
                main_config.objects.all().delete()
                main_config.objects.create(**main_config)
                content = "Success"
            else:
                content = test_ret['output']

            reload_config()
        else:
            content = "ArgsError"
    except Exception, e:
        content = str(e)

    return HttpResponse(content)
    pass
#
