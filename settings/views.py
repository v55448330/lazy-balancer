from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.http import HttpResponse
from proxy.models import *
from main.models import *
from lazy_balancer.views import is_auth
from nginx.ip import set_firewall
from nginx.views import reload_config
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
        'nics':get_sys_info()['nic'],
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
                content = { "flag":"Error","context":"VerifyFaild" }
    except Exception,e:
        content = { "flag":"Error","context":str(e) }

    return HttpResponse(json.dumps(content))

@is_auth
def admin_reset(request):
    try:
        post = json.loads(request.body)
        reset = post['reset']
        if reset == 1:
            User.objects.all().delete()
            content = { "flag":"Success" }
    except Exception,e:
        content = { "flag":"Error","context":str(e) }

    return HttpResponse(json.dumps(content))

@is_auth
def select_nic(request):
    try:
        post = json.loads(request.body)
        internal_nic = post['select_nic']
        if system_settings.objects.all().count() != 0:
            system_settings.objects.all().update(internal_nic=internal_nic)
        else:
            system_settings.objects.create(internal_nic=internal_nic)
        set_firewall()
        content = { "flag":"Success" }
    except Exception,e:
        content = { "flag":"Error","context":str(e) }
    return HttpResponse(json.dumps(content))

@is_auth
def config_backup(request,action):
    main_config_qc = main_config.objects.all()
    upstream_config_qc = upstream_config.objects.all()
    proxy_config_qc = proxy_config.objects.all()
    if action == "export":
        try:
            m_config = serializers.serialize('json', main_config_qc)
            u_config = serializers.serialize('json', upstream_config_qc)
            p_config = serializers.serialize('json', proxy_config_qc)

            config = {
                "main_config" : m_config,
                "upstream_config" : u_config,
                "proxy_config" : p_config,
            }
            content = { "flag":"Success", "context": config }
        except Exception,e:
            content = { "flag":"Error","context":str(e) }

    elif action == "import":
        try:
            post = json.loads(request.body)

            m_config = post['main_config']
            u_config = post['upstream_config']
            p_config = post['proxy_config']

            main_config_qc.delete()
            upstream_config_qc.delete()
            proxy_config_qc.delete()

            for obj in serializers.deserialize("json", m_config):
                obj.save()
            for obj in serializers.deserialize("json", u_config):
                obj.save()
            for obj in serializers.deserialize("json", p_config):
                obj.save()

            reload_config()

            content = { "flag":"Success" }
        except Exception,e:
            content = { "flag":"Error","context":str(e) }

    return HttpResponse(json.dumps(content))
