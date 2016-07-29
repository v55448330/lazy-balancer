from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.http import HttpResponse
from django.db.models import Q
from lazy_balancer.views import is_auth
from proxy.models import proxy_config,upstream_config
from settings.models import system_settings
from nginx.views import *
from nginx.ip import *
import json
import uuid
import time
import os

@login_required(login_url="/login/")
def view(request):
    filter = request.GET.get('filter',"")
    if filter:
        p_config = proxy_config.objects.filter(Q(proxy_name__contains=filter)|Q(server_name__contains=filter))
    else:
        p_config = proxy_config.objects.all()

    NUM_PER_PAGE = 8
    paginator = Paginator(p_config, NUM_PER_PAGE)
    page = request.GET.get('page')

    try:
        contents = paginator.page(page)
    except PageNotAnInteger:
        contents = paginator.page(1)
    except EmptyPage:
        contents = paginator.page(paginator.num_pages)

    user = {
        'name':request.user,
        'date':time.time()
    }

    return render_to_response('proxy/view.html',{ 'proxy' : contents, 'filter' : filter, 'user' : user })
    pass

@is_auth
def query_proxy(request):
    try:
        post = json.loads(request.body)
        proxy = proxy_config.objects.get(config_id=post['config_id'])
        p = {
            'proxy_name':proxy.proxy_name,
            'config_id':proxy.config_id,
            'listen':proxy.listen,
            'server_name':proxy.server_name,
            'access_log':proxy.access_log,
            'error_log':proxy.error_log,
            'protocols':proxy.protocols,
            'ssl_cert':proxy.ssl_cert,
            'ssl_key':proxy.ssl_key,
            'description':proxy.description,
            'balancer_type':proxy.balancer_type,
        }
        u = []
        for ui in proxy.upstream_list.all():
            u.append({
                'address':ui.address,
                'port':ui.port,
                'weight':ui.weight,
                'max_fails':ui.max_fails,
                'fail_timeout':ui.fail_timeout
            })
            pass
        content = { "flag":"Success","content":{"proxy":p,"upstream":u}}
    except Exception, e:
        content = { "flag":"Error","content":str(e) }
    return HttpResponse(json.dumps(content))
    pass

@is_auth
def delete_proxy(request):
    try:
        post = json.loads(request.body)
        proxy = proxy_config.objects.get(pk=post['pk'])
        proxy.delete()
        reload_config()
        content = { "flag":"Success" }
    except Exception, e:
        content = { "flag":"Error","content":str(e) }
    return HttpResponse(json.dumps(content))
    pass

@is_auth
def change_status(request):
    try:
        post = json.loads(request.body)
        proxy = proxy_config.objects.get(pk=post['pk'])
        proxy.status = bool(int(post['status']))
        proxy.save()
        reload_config()
        content = { "flag":"Success" }
    except Exception, e:
        content = { "flag":"Error","content":str(e) }

    return HttpResponse(json.dumps(content))
    pass

@is_auth
def save(request):
    try:
        post = json.loads(request.body)
        config_id = post['base_config']['proxy_config_id']
        access_log = post['base_config']['proxy_access_log']
        error_log = post['base_config']['proxy_error_log']
        proxy_name = post['base_config']['proxy_proxy_name']
        listen = post['base_config']['proxy_listen']
        server_name = post['base_config']['proxy_server_name']
        description = post['base_config']['proxy_description']
        balancer_type = ""

        nic = False
        if system_settings.objects.all().count() != 0:
            if system_settings.objects.all()[0].internal_nic != "":
                nic = True

        if nic:
            if proxy_name and server_name and listen and len(post['upstream_list']) and not listen=="8000":
                create_flag = False
                if config_id == "0":
                    config_id = str(uuid.uuid1())
                    create_flag = True

                config_nginx_path = "/etc/nginx/nginx.conf"
                config_path = "/etc/nginx/conf.d/%s.conf" % config_id

                if not access_log:
                    access_log = "/var/log/nginx/access-%s.log" % config_id

                if not error_log:
                    error_log = "/var/log/nginx/error-%s.log" % config_id

                if post['base_config'].has_key('proxy_ip_hash'):
                    balancer_type = "ip_hash"

                proxy = {
                    'config_id' : config_id,
                    'proxy_name' : proxy_name,
                    'status' : False,
                    'listen' : int(listen),
                    'server_name' : server_name,
                    'access_log' : access_log,
                    'error_log' : error_log,
                    'balancer_type' : balancer_type,
                    'update_time' : time.time(),
                    'description' : description,
                    'protocols' : False,
                    'ssl_cert' : "",
                    'ssl_cert_path' : "",
                    'ssl_key' : "",
                    'ssl_key_path' : "",
                }

                if post['ssl_config'].has_key('ssl_status'):
                    cert_path = "/etc/nginx/conf.d/%s.crt" % config_id
                    key_path = "/etc/nginx/conf.d/%s.key" % config_id
                    cert_body = post['ssl_config']['ssl_cert_body']
                    key_body = post['ssl_config']['ssl_key_body']
                    if cert_body and key_body:
                        write_config(cert_path,cert_body)
                        write_config(key_path,key_body)
                        proxy['protocols'] = True
                        proxy['ssl_cert'] = cert_body
                        proxy['ssl_cert_path'] = cert_path
                        proxy['ssl_key'] = key_body
                        proxy['ssl_key_path'] = key_path
                        if not post['ssl_config'].has_key('ssl_port'):
                            proxy['listen'] = 443
                else:
                    if proxy['listen'] == 443:
                        proxy['listen'] = 80

                upstream_list = []

                for upstream in post['upstream_list']:
                    weight = upstream['upstream_weight']
                    fail_timeout = upstream['upstream_fail_timeout']
                    max_fails = upstream['upstream_max_fails']

                    if not weight:
                        weight = 10

                    if not fail_timeout:
                        fail_timeout = 5

                    if not max_fails:
                        max_fails = 3

                    upstream_list.append({
                        'status' : True,
                        'address' : upstream['upstream_address'],
                        'port' : int(upstream['upstream_port']),
                        'weight' : int(weight),
                        'max_fails' : int(max_fails),
                        'fail_timeout' : int(fail_timeout),
                    })

                p_config = { 'proxy' : proxy, 'upstream' : upstream_list }
                config_content = build_proxy_config(p_config)
                write_config(config_path,config_content)

                test_ret = test_config()
                if test_ret['status'] == 0:
                    #if len(_old_p_config) != 0:
                    #    old_p_config.delete()

                    proxy['status'] = True
                    if create_flag:
                        obj_p_config = proxy_config.objects.create(**proxy)
                    else:
                        proxy_config.objects.filter(config_id=config_id).update(**proxy)
                        obj_p_config = proxy_config.objects.get(config_id=config_id)

                    obj_p_config.upstream_list.all().delete()
                    for up in upstream_list:
                        obj_p_config.upstream_list.add(upstream_config.objects.create(**up))
                        obj_p_config.save()
                        pass

                    set_firewall()
                    content = {"flag":"Success"}
                else:
                    content = {"flag":"Error","content":test_ret['output']}

                reload_config()
            else:
                content = {"flag":"Error","content":"ArgsError"}
        else:
            content = {"flag":"Error","content":"NicError"}

    except Exception, e:
        content = {"flag":"Error","content":str(e)}

    return HttpResponse(json.dumps(content))
    pass
