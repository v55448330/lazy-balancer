from django.shortcuts import render, render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django.http import HttpResponse
from nginx_balancer.views import is_auth
from nginx.views import *
import json
import time

@login_required(login_url="/login/")
def view(request):
    _sysinfo = get_sysinfo()
    _user = {
        'name':request.user,
        'date':time.time()
    }
    return render_to_response('dashboard/view.html',{'sysinfo' : _sysinfo, 'user' : _user})

@is_auth
def get_status_info(request):
    content = {
        'flag':"Success",
        'content':get_statusinfo()
    }
    return HttpResponse(json.dumps(content))
