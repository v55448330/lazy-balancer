from django.shortcuts import render, render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.http import HttpResponse
from lazy_balancer.views import is_auth
from nginx.views import *
import json
import time

@login_required(login_url="/login/")
def view(request):
    user = {
        'name':request.user,
        'date':time.time()
    }
    return render_to_response('dashboard/view.html',{'user' : user})

@is_auth
def get_status_info(request):
    context = {
        'flag':"Success",
        'context':{
            "sysstatus" : get_sys_status(),
            "reqstatus" : get_req_status(),
            "sysinfo": get_sys_info() 
        }
    }
    return HttpResponse(json.dumps(context))

@is_auth
def service(request):
    if request.method == 'POST':
        try:
            post = json.loads(request.body.decode('utf-8'))
            action = post.get('action')
            if action in ('start', 'stop'):
                if nginx_control(action):
                    context = {'flag':"Success"}

        except Exception as e:
            context = {"flag": "Error", "context": str(e)}

    else:
        context = {"flag": "Error", "context": "method is denied"}

    return HttpResponse(json.dumps(context))


@is_auth
def reset_req_status(request):
    resp = delete_vts_zone()
    if resp: 
        context = {'flag':"Success"}
    else:
        context = {'flag':"Error"}
    return HttpResponse(json.dumps(context))
