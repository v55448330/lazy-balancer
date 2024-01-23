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
    sysinfo = get_sys_info()
    user = {
        'name':request.user,
        'date':time.time()
    }
    return render_to_response('dashboard/view.html',{'sysinfo' : sysinfo, 'user' : user})

@is_auth
def get_status_info(request):
    req_status = get_req_status()
    context = {
        'flag':"Success",
        'context':{
            "sysstatus" : get_sys_status(),
            "reqstatus" : req_status
        }
    }
    return HttpResponse(json.dumps(context))

@is_auth
def reset_req_status(request):
    resp = delete_vts_zone()
    if resp: 
        context = {'flag':"Success"}
    else:
        context = {'flag':"Error"}
    return HttpResponse(json.dumps(context))
