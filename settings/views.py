from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from lazy_balancer.views import is_auth
from nginx.ip import set_firewall
from .models import system_settings
from nginx.views import *
import json
import time

@login_required(login_url="/login/")
def view(request):

    user = {
        'name':request.user,
        'date':time.time()
    }
    nic = {
        'nics':get_sysinfo()['nic'],
        'internal_nic':''
    }

    if system_settings.objects.all().count() != 0:
        settings = system_settings.objects.all()[0]
        nic['internal_nic'] = settings.internal_nic

    return render_to_response('settings/view.html',{ 'user' : user , 'nic' : nic })

@is_auth
def modify_pass(request):
    try:
        post = json.loads(request.body)
        old_pass = post['old_password']
        new_pass = post['new_password']
        verify_pass = post['verify_password']
        if old_pass and new_pass and verify_pass:
            user = User.objects.get(username=request.user)
            if user.check_password(old_pass) and new_pass == verify_pass:
                user.set_password(verify_pass)
                user.save()
                content = { "flag":"Success" }
            else:
                content = { "flag":"Error","content":"VerifyFaild" }
    except Exception,e:
        content = { "flag":"Error","content":str(e) }

    return HttpResponse(json.dumps(content))

@is_auth
def select_nic(request):
    try:
        content = "test"
        post = json.loads(request.body)
        internal_nic = post['select_nic']
        if system_settings.objects.all().count() != 0:
            system_settings.objects.all().update(internal_nic=internal_nic)
        else:
            system_settings.objects.create(internal_nic=internal_nic)
        set_firewall()
        content = { "flag":"Success" }
    except Exception,e:
        content = { "flag":"Error","content":str(e) }
    return HttpResponse(json.dumps(content))
