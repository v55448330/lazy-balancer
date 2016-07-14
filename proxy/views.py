from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.http import HttpResponse
from proxy.models import proxy_config,upstream_config
from nginx.views import *
import json
import uuid
import time
import os
 
def view(request):
    _proxy_config = proxy_config.objects.all()

    return render_to_response('proxy/view.html',{ 'proxy' : _proxy_config })
    pass

def query_proxy(request):
    try:
        _post = json.loads(request.body)
        _proxy = proxy_config.objects.get(config_id=_post['config_id'])
        _p = {
            'proxy_name':_proxy.proxy_name,
            'config_id':_proxy.config_id,
            'listen':_proxy.listen,
            'server_name':_proxy.server_name,
            'access_log':_proxy.access_log,
            'error_log':_proxy.error_log,
            'balancer_type':_proxy.balancer_type,
        }
        _u = []
        for _ui in _proxy.upstream_list.all():
            _u.append({
                'address':_ui.address,
                'port':_ui.port,
                'weight':_ui.weight,
                'max_fails':_ui.max_fails,
                'fail_timeout':_ui.fail_timeout
            })
            pass
        content = { "flag":"Success","proxy":_p,"upstream":_u}
    except Exception, e:
        content = { "flag":"Error","content":str(e) }
    return HttpResponse(json.dumps(content))
    pass

def delete_proxy(request):
    try:
        _post = json.loads(request.body)
        _proxy = proxy_config.objects.get(pk=_post['pk'])
        _proxy.delete()
        reload_config()
        content = "Success"
    except Exception, e:
        content = str(e)
    return HttpResponse(content)
    pass

def change_status(request):
    try:
        _post = json.loads(request.body)
        _proxy = proxy_config.objects.get(pk=_post['pk'])
        _proxy.status = bool(int(_post['status']))
        _proxy.save()
        reload_config()
        content = "Success"
    except Exception, e:
        content = str(e)

    return HttpResponse(content)
    pass


def save(request):
    content = "" 
    try:
        _post = json.loads(request.body)
        print _post
        _config_id = _post['base_config']['proxy_config_id']
        _access_log = _post['base_config']['proxy_access_log']
        _error_log = _post['base_config']['proxy_error_log']
        _proxy_name = _post['base_config']['proxy_proxy_name']
        _listen = _post['base_config']['proxy_listen']
        _server_name = _post['base_config']['proxy_server_name']
        _balancer_type = ""
        
        if _proxy_name and _server_name and _listen and len(_post['upstream_list']):
            if _config_id == "0":
                _config_id = str(uuid.uuid1())

            _config_nginx_path = "/etc/nginx/nginx.conf"
            _config_path = "/etc/nginx/conf.d/%s.conf" % _config_id

            if not _access_log:
                _access_log = "/var/log/nginx/access-%s.log" % _config_id

            if not _error_log:
                _error_log = "/var/log/nginx/error-%s.log" % _config_id

            if _post['base_config'].has_key('proxy_ip_hash'):
                _balancer_type = "ip_hash"

            _proxy = {
                'config_id' : _config_id,
                'proxy_name' : _proxy_name,
                'status' : False,
                'listen' : int(_listen),
                'server_name' : _server_name,
                'access_log' : _access_log,
                'error_log' : _error_log,
                'balancer_type' : _balancer_type,
                'update_time' : time.time()
            }

            _upstream_list = []

            for _upstream in _post['upstream_list']:
                _weight = _upstream['upstream_weight']
                _fail_timeout = _upstream['upstream_fail_timeout']
                _max_fails = _upstream['upstream_max_fails']

                if not _weight:
                    _weight = 10

                if not _fail_timeout:
                    _fail_timeout = 5

                if not _max_fails:
                    _max_fails = 3

                _upstream_list.append({
                    'status' : True,
                    'address' : _upstream['upstream_address'],
                    'port' : int(_upstream['upstream_port']),
                    'weight' : int(_weight),
                    'max_fails' : int(_max_fails),
                    'fail_timeout' : int(_fail_timeout),
                })
                pass

            _proxy_config = { 'proxy' : _proxy, 'upstream' : _upstream_list }
            _config_content = build_proxy_config(_proxy_config)
            write_config(_config_path,_config_content)

            _test_ret = test_config()
            if _test_ret['status'] == 0:
                _old_proxy_config = proxy_config.objects.filter(config_id=_config_id)
                if len(_old_proxy_config) != 0:
                    _old_proxy_config.delete()

                _proxy['status'] = True
                proxy_config.objects.create(**_proxy)
                
                _proxy = proxy_config.objects.get(config_id=_config_id)
                _proxy.upstream_list.all().delete()
                for _up in _upstream_list:
                    _proxy.upstream_list.add(upstream_config.objects.create(**_up))
                    _proxy.save()
                    pass
                content = "Success"
            else:
                content = _test_ret['output']

            reload_config()
        else:
            content = "ArgsError"

    except Exception, e:
        content = str(e)

    return HttpResponse(content)
    pass
#
