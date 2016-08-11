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
    r_stat = []
    for r in req_status:
        rs = {
            'req_url' : r[0],
            'bytes_in' : r[2],
            'bytes_out' : r[3],
            'conn_total' : r[4],
            'req_total' : r[5],
            'http_2xx' : r[6],
            'http_3xx' : r[7],
            'http_4xx' : r[8],
            'http_5xx' : r[9]
        }
        r_stat.append(rs)
    context = {
        'flag':"Success",
        'context':{
            "sysstatus" : get_sys_status(),
            "reqstatus" : r_stat
        }
    }
    return HttpResponse(json.dumps(context))
