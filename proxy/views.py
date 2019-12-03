from urlparse import urlparse
from OpenSSL import crypto
from dateutil import parser
from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.db.models import Q
from lazy_balancer.views import is_auth
from proxy.models import proxy_config,upstream_config
from main.models import main_config
from settings.models import system_settings
from nginx.views import *
import json
import uuid
import time
import os

@login_required(login_url="/login/")
def view(request):
    filter = request.GET.get('filter',"")
    if filter:
        p_config = proxy_config.objects.filter(Q(proxy_name__contains=filter)|Q(server_name__contains=filter)|Q(config_id__contains=filter)|Q(listen__contains=filter))
    else:
        p_config = proxy_config.objects.all()

    NUM_PER_PAGE = 10
    paginator = Paginator(p_config, NUM_PER_PAGE)
    page = request.GET.get('page')

    try:
        contexts = paginator.page(page)
    except PageNotAnInteger:
        contexts = paginator.page(1)
    except EmptyPage:
        contexts = paginator.page(paginator.num_pages)

    user = {
        'name':request.user,
        'date':time.time()
    }

    return render_to_response('proxy/view.html',{ 'proxy' : contexts, 'filter' : filter, 'user' : user })
    pass

@is_auth
def check_http_status(request):
    try:
        post = json.loads(request.body)
        status = get_proxy_http_status()

        if status.has_key('servers'):
            status = status['servers']['server']
        else:
            status = []

        if post['pk'] == 0:
            content = { "flag":"Success","status":status}
        else:
            proxy = proxy_config.objects.get(pk=post['pk'])
            content = { "flag":"Success","config_id":proxy.config_id,"status":status}
        
    except Exception, e:
        content = { "flag":"Error","context":str(e) }
    return HttpResponse(json.dumps(content))
    pass

@is_auth
def query_proxy(request):
    try:
        post = json.loads(request.body)
        proxy = proxy_config.objects.get(config_id=post['config_id'])
        p = model_to_dict(proxy)
        del p['upstream_list']
        u = []
        for ul in proxy.upstream_list.all():
            u.append(model_to_dict(ul))
        content = { "flag":"Success","context":{"proxy":p,"upstream":u}}
    except Exception, e:
        content = { "flag":"Error","context":str(e) }
    return HttpResponse(json.dumps(content))
    pass

@is_auth
def delete_proxy(request):
    try:
        post = json.loads(request.body)
        p = proxy_config.objects.filter(pk=post['pk'])
        p.delete()
        reload_config("proxy")
        content = { "flag":"Success" }
    except Exception, e:
        content = { "flag":"Error","context":str(e) }
    return HttpResponse(json.dumps(content))
    pass

@is_auth
def change_status(request):
    try:
        post = json.loads(request.body)
        proxy = proxy_config.objects.get(pk=post['pk'])
        proxy.status = bool(int(post['status']))
        proxy.save()
        reload_config("proxy")
        content = { "flag":"Success" }
    except Exception, e:
        content = { "flag":"Error","context":str(e) }

    return HttpResponse(json.dumps(content))
    pass

@is_auth
def proxy_logs(request):
    try:
        post = json.loads(request.body)

        curr_position = {"access":0,"error":0}
        curr_position['access'] = int(post['curr_position']['access'])
        curr_position['error'] = int(post['curr_position']['error'])

        proxy = proxy_config.objects.get(pk=post['pk'])

        log_body = {"access":"","error":""}

        with open(proxy.access_log) as file_:
            file_.seek(0,2)

            if curr_position['access'] != 0:
                file_.seek(curr_position['access'])
                line = file_.readline()

                while line:
                    log_body['access'] += line
                    curr_position['access'] = file_.tell()
                    line = file_.readline()

            curr_position['access'] = file_.tell()

        if proxy.protocol == 'http':
            with open(proxy.error_log) as file_:
                file_.seek(0,2)

                if curr_position['error'] != 0:
                    file_.seek(curr_position['error'])
                    line = file_.readline()

                    while line:
                        log_body['error'] += line
                        curr_position['error'] = file_.tell()
                        line = file_.readline()

                curr_position['error'] = file_.tell()
        else:
            log_body['error'] == 'None'
            curr_position['error'] = 0
        
        content = { "flag":"Success" , "log_body":log_body , "curr_position":curr_position }
    except Exception, e:
        content = { "flag":"Error","context":str(e) }

    return HttpResponse(json.dumps(content))
    pass

@is_auth
def save(request):
    try:
        post = json.loads(request.body)
        # print(str(post))
        # content = {"flag":"Debug","context":"Debug"}
        # return HttpResponse(json.dumps(content))
        if not len(main_config.objects.all()):
            content = {"flag":"Error","context":"MainConfigNotFound"}
            return HttpResponse(json.dumps(content))

        config_id = post['base_config']['proxy_config_id']
        proxy_name = post['base_config']['proxy_proxy_name']
        proxy_protocol = post['base_config']['proxy_protocol']
        listen = post['base_config']['proxy_listen']
        server_name = post['base_config'].get('proxy_server_name','')
        access_log = post['base_config']['proxy_access_log']
        error_log = post['base_config']['proxy_error_log']
        description = post['base_config']['proxy_description']

        if post['base_config'].has_key('upstream_backend_domain_toggle'):
            bd = post['base_config'].get('upstream_backend_domain').lower()
            if "http://" in bd or "https" in bd:
                host = urlparse(bd).netloc
            else:
                host = urlparse(bd).path
            backend_domain = host
            upstream_backend_domain_toggle = True
        else:
            backend_domain = ''
            upstream_backend_domain_toggle = False
            host = server_name.split(' ')[0]

        balancer_type = ""

        if proxy_name and listen and len(post['upstream_list']) and proxy_protocol and not listen=="8000":
            create_flag = False
            if config_id == "0":
                config_id = str(uuid.uuid1())
                create_flag = True

            # config_nginx_path = "/etc/nginx/nginx.conf"
            # config_path = "/etc/nginx/conf.d/%s.conf" % config_id

            if not access_log:
                access_log = "/var/log/nginx/access-%s.log" % config_id

            if not error_log:
                error_log = "/var/log/nginx/error-%s.log" % config_id

            if post['base_config'].has_key('upstream_ip_hash'):
                balancer_type = "ip_hash"

            if post['base_config'].has_key('upstream_http_check'):
                http_check = True
            else:
                http_check = False

            if post['base_config'].has_key('proxy_gzip'):
                gzip = True
            else:
                gzip = False

            if post['base_config'].has_key('upstream_backend_protocol'):
                backend_protocol = "https"
            else:
                backend_protocol = "http"

            if proxy_protocol == 'tcp':
                server_name = ''
                check_type = False
                gzip = False
                protocol = False # HTTP is True, TCP is False
                backend_protocol = "tcp"
                port_list = list(proxy_config.objects.values_list('listen', flat=True))
                port_list.append(8000)
                if listen in port_list:
                    content = {"flag":"Error","context":"Port occupied"}
                    return HttpResponse(json.dumps(content))
                config_path = "/etc/nginx/conf.d/%s-tcp.conf" % config_id
            else:
                if not server_name:
                    content = {"flag":"Error","context":"Server Name not Found"}
                    return HttpResponse(json.dumps(content))
                protocol = True
                config_path = "/etc/nginx/conf.d/%s-http.conf" % config_id

            proxy = {
                'config_id' : config_id,
                'proxy_name' : proxy_name,
                'protocol': protocol,
                'listen' : int(listen),
                'server_name' : server_name,
                'host' : host,
                'access_log' : access_log,
                'error_log' : error_log,
                'balancer_type' : balancer_type,
                'http_check' : http_check,
                'gzip' : gzip,
                'description' : description,
                'ssl' : False,
                'ssl_cert' : "",
                'ssl_cert_path' : "",
                'ssl_key' : "",
                'ssl_key_path' : "",
                'custom_config' : "",
                'backend_protocol' : backend_protocol,
                'backend_domain_toggle' : upstream_backend_domain_toggle,
                'backend_domain' : backend_domain,
                'update_time' : time.time(),
                'status' : False,
            }

            if post['ssl_config'].has_key('ssl_status'):
                cert_path = "/etc/nginx/conf.d/%s.crt" % config_id
                key_path = "/etc/nginx/conf.d/%s.key" % config_id
                cert_body = post['ssl_config']['ssl_cert_body']
                key_body = post['ssl_config']['ssl_key_body']

                if post['ssl_config'].has_key('ssl_http2'):
                    ssl_http2 = True
                else:
                    ssl_http2 = False

                if post['ssl_config'].has_key('ssl_redirect_https'):
                    ssl_redirect_https = True
                else:
                    ssl_redirect_https = False

                if cert_body and key_body:
                    proxy['ssl'] = True
                    proxy['ssl_http2'] = ssl_http2
                    proxy['ssl_redirect_https'] = ssl_redirect_https
                    proxy['ssl_cert'] = cert_body
                    proxy['ssl_cert_path'] = cert_path
                    proxy['ssl_key'] = key_body
                    proxy['ssl_key_path'] = key_path
                    if not post['ssl_config'].has_key('ssl_port'):
                        proxy['listen'] = 443
                    else:
                        port_list = list(proxy_config.objects.filter(protocol=True,ssl=False).values_list('listen', flat=True))
                        port_list.append(8000)
                        if proxy['listen'] in port_list:
                            content = {"flag":"Error","context":"Port occupied"}
                            return HttpResponse(json.dumps(content))
                    write_config(cert_path,cert_body)
                    write_config(key_path,key_body)
            else:
                if proxy['listen'] == 443:
                    proxy['listen'] = 80
            
            if post['custom_config']:
                proxy['custom_config'] = post.get('custom_config', '')

            fail_timeout = post['base_config'].get('upstream_fail_timeout',0)
            max_fails = post['base_config'].get('upstream_max_fails',0)

            if not fail_timeout:
                fail_timeout = 5

            if not max_fails:
                max_fails = 3
            
            proxy['fail_timeout'] = int(fail_timeout)
            proxy['max_fails'] = int(max_fails)

            upstream_list = []

            for upstream in post['upstream_list']:
                weight = upstream['upstream_weight']

                if not weight:
                    weight = 10

                upstream_list.append({
                    'status' : True,
                    'address' : upstream['upstream_address'],
                    'port' : int(upstream['upstream_port']),
                    'weight' : int(weight)
                })

            p_config = { 'proxy' : proxy, 'upstream' : upstream_list }

            config_context = build_proxy_config(p_config)
            write_config(config_path,config_context)

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

                content = {"flag":"Success"}
            else:
                content = {"flag":"Error","context":test_ret['output']}

            reload_config("proxy")

        else:
            content = {"flag":"Error","context":"ArgsError"}
            return HttpResponse(json.dumps(content))

    except Exception, e:
        content = {"flag":"Error","context":str(e)}

    return HttpResponse(json.dumps(content))
    pass

# @is_auth
def get_cert_status(request):
    try:
        post = json.loads(request.body)
        proxy = proxy_config.objects.get(pk=post['pk'])
        cert_file_path = '/etc/nginx/conf.d/%s.crt' % proxy.config_id
        # print(cert_file_path)
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(cert_file_path).read())
        cert_issuer = cert.get_issuer()
        cert_info = {
            'subject': cert.get_subject().CN,
            'issuer' : "%s/%s/%s" % (cert_issuer.C,cert_issuer.O,cert_issuer.CN),
            'datetime_struct' : parser.parse(cert.get_notAfter().decode("UTF-8")).strftime('%Y-%m-%d %H:%M:%S'),
            'has_expired' : cert.has_expired()
        }

        content = { "flag":"Success","config_id":proxy.config_id,"cert_info":cert_info}
    except Exception, e:
        content = { "flag":"Error","context":str(e) }
    return HttpResponse(json.dumps(content))
    pass