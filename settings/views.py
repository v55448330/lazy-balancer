from django.shortcuts import render, render_to_response
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.http import HttpResponse
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from proxy.models import *
from main.models import *
from lazy_balancer.views import is_auth
from nginx.views import reload_config
from settings.models import system_settings, sync_status
from datetime import datetime
from nginx.views import *
import logging
import uuid
import json
import time
import hashlib

logger = logging.getLogger('django')

try:  
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    register_events(scheduler)
    scheduler.start()
except Exception as e:
    logger.error(str(e))
    scheduler.shutdown()

@login_required(login_url="/login/")
def view(request):
    user = {
        'name':request.user,
        'date':time.time()
    }

    _system_settings = system_settings.objects.all()
    _sync_status = sync_status.objects.all()
    if len(_system_settings) == 0:
        system_settings.objects.create(config_sync_type=0)
        _system_settings = system_settings.objects.all()
    
    return render_to_response('settings/view.html', {'user': user, 'settings': _system_settings[0], 'sync_status': _sync_status})

@is_auth
def sync_config(request):
    try:
        post = json.loads(request.body.decode('utf-8'))
        if save_sync(post):
            content = {"flag": "Success"}
        else:
            content = {"flag": "Error", "context": "input error"}

    except Exception as e:
        content = {"flag": "Error", "context": str(e)}

    return HttpResponse(json.dumps(content))

def save_sync(config):
    try:
        s_config = system_settings.objects.all()[0]
        if int(config.get('config_sync_type')) == 0:
            s_config.config_sync_type = 0
            s_config.config_sync_access_key = None
            s_config.config_sync_master_url = None
            s_config.config_sync_scope = None
            DjangoJobStore().remove_all_jobs()
            scheduler.remove_all_jobs()
        elif int(config.get('config_sync_type')) == 1:
            if not s_config.access_key:
                s_config.update_access_key()
            s_config.config_sync_type = 1
            s_config.config_sync_master_url = None
            s_config.config_sync_scope = None
            scheduler.add_job(sync, 'interval', seconds=60, name='sync', id='sync', replace_existing=True)
        elif int(config.get('config_sync_type')) == 2:
            if config.get('config_sync_master_api'):
                sync_interval = config.get('config_sync_interval')
                if not sync_interval:
                    sync_interval = 60
                else:
                    sync_interval = int(sync_interval)
                s_config.config_sync_type = 2
                s_config.config_sync_master_url = config.get('config_sync_master_api').strip('/')
                s_config.config_sync_access_key = config.get('config_sync_access_key') 
                s_config.config_sync_interval = sync_interval
                s_config.config_sync_scope = bool(config.get('config_sync_scope', ''))
                scheduler.add_job(sync, 'interval', seconds=sync_interval, name='sync', id='sync', replace_existing=True)
            else:
                return False
        else:
            return False

        s_config.save()
        return True
    except Exception as e:
        logger.error(str(e))
        return False

@is_auth
def admin_password(request, action):
    if action == "reset":
        try:
            User.objects.all().delete()
            content = { "flag":"Success" }
        except Exception as e:
            content = { "flag":"Error","context":str(e) }

    elif action == "modify":
        try:
            post = json.loads(request.body.decode('utf-8'))
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

        except Exception as e:
            content = { "flag":"Error","context":str(e) }

    return HttpResponse(json.dumps(content))

def get_config(scope=0):
    try:
       # scope: [0, 1, 2]
        # 0 - proxy/upstream config
        # 1 - main/proxy/upstream config
        # 2 - system/main/proxy/upstream config

        if isinstance(scope, int):
            upstream_config_qc = upstream_config.objects.all()
            proxy_config_qc = proxy_config.objects.all()

            config = {
                "main_config" : {"sha1":"", "config":""},
                "system_config" : {"sha1":"", "config":""},
                "upstream_config" : {"sha1":"", "config":""}, 
                "proxy_config" : {"sha1":"", "config":""}
            }

            if upstream_config_qc:
                u_config = serializers.serialize('json', upstream_config_qc)
                config['upstream_config'] = {"sha1":hashlib.sha1(u_config.encode('utf-8')).hexdigest(), "config": u_config}

            if proxy_config_qc:
                p_config = serializers.serialize('json', proxy_config_qc)
                config['proxy_config'] = {"sha1":hashlib.sha1(p_config.encode('utf-8')).hexdigest(), "config": p_config}
 
            if scope >= 1:
                main_config_qc = main_config.objects.all()
                m_config = serializers.serialize('json', main_config_qc)
                config['main_config'] = {"sha1":hashlib.sha1(m_config.encode('utf-8')).hexdigest(), "config": m_config}

            if scope >= 2:
                system_config_qc = system_settings.objects.all()
                s_config = serializers.serialize('json', system_config_qc)
                config['system_config'] = {"sha1":hashlib.sha1(s_config.encode('utf-8')).hexdigest(), "config": s_config}
            
        return config
        
    except Exception as e:
        print(str(e))
        return None
    
def import_config(config, restore=0):
    try:
        main_config_qc = main_config.objects.all()
        system_config_qc = system_settings.objects.all()
        proxy_config_qc = proxy_config.objects.all()
        upstream_config_qc = upstream_config.objects.all()
        if restore:
            clean_dir("/etc/nginx/conf.d")
            main_config_qc.delete()
            system_config_qc.delete()
            proxy_config_qc.delete()
            upstream_config_qc.delete()
        else:
            logger.info('get backup config...')
            config_bak = get_config(2)

        m_config = config['main_config']
        s_config = config['system_config']
        p_config = config['proxy_config']
        u_config = config['upstream_config']

        config_count = 0
        error_count = 0
        if m_config.get('config', False):
            if hashlib.sha1(serializers.serialize('json', main_config_qc).encode('utf-8')).hexdigest() == m_config.get('sha1'):
                logger.info('main config no change!')
            else:
                if hashlib.sha1(m_config.get('config').encode('utf-8')).hexdigest() == m_config.get('sha1'):
                    logger.info('import main config started...')
                    main_config_bak = main_config_qc
                    main_config_qc.delete()
                    for obj in serializers.deserialize("json", m_config.get('config')):
                        obj.save()
                    if reload_config("main", 1):
                        logger.info('import main config finished!')
                    else:
                        logger.info('import main config error!')
                        error_count += 1
                    config_count += 1
                else:
                    logger.error('main config hash check faild')
                    error_count += 1

        if s_config.get('config', False):
            if hashlib.sha1(serializers.serialize('json', system_config_qc).encode('utf-8')).hexdigest() == s_config.get('sha1'):
                logger.info('system config no change!')
            else:
                if hashlib.sha1(s_config.get('config').encode('utf-8')).hexdigest() == s_config.get('sha1'):
                    logger.info('import system config started...')
                    system_config_qc.delete()
                    for obj in serializers.deserialize("json", s_config.get('config')):
                        obj.save()
                    logger.info('import system config finished!')
                    config_count += 1
                else:
                    logger.error('system config hash check faild')
                    error_count += 1

        if p_config.get('config', False) and u_config.get('config', False):
            if hashlib.sha1(serializers.serialize('json', proxy_config_qc).encode('utf-8')).hexdigest() == p_config.get('sha1') and hashlib.sha1(serializers.serialize('json', upstream_config_qc).encode('utf-8')).hexdigest() == u_config.get('sha1'):
                logger.info('proxy config and upstream config no change!')
            else:
                if hashlib.sha1(p_config.get('config').encode('utf-8')).hexdigest() == p_config.get('sha1') and hashlib.sha1(u_config.get('config').encode('utf-8')).hexdigest() == u_config.get('sha1'):
                    logger.info('import upstream config started...')
                    upstream_config_qc.delete()
                    for obj in serializers.deserialize("json", u_config.get('config')):
                        obj.save()
                    logger.info('import upstream config finished!')

                    logger.info('import proxy config started...')
                    proxy_config_qc.delete()
                    for obj in serializers.deserialize("json", p_config.get('config')):
                        obj.save()

                    if reload_config("proxy", 1):
                        logger.info('import proxy config finished!')
                    else:
                        logger.info('import proxy config error!')
                        error_count += 1
                    config_count += 1
                else:
                    logger.error('proxy or upstream config hash check faild')
                    error_count += 1

        if error_count:
            logger.error('config import error! restore backup ...')
            if import_config(config_bak, 1):
                logger.info('config import restore backup finished.') 
            else:
                logger.error('config import restore backup failed!') 
            return False
        
        if config_count:
            logger.info('config import finished.')
        else:
            logger.info('all config no change! config import finished.')

        return True
    except Exception as e:
        logger.error(str(e))
        return False

def sync():
    sync_status.objects.all().delete()
    settings = system_settings.objects.last()
    if settings.config_sync_type == 1:
        logger.info('check syncing task')
        for status in sync_status.objects.all():
            if (datetime.now() - status.update_time).seconds >= 30 and status.status == 1:
                logger.info('syncing task [%s] timeout', status.address)
                status.status = 3
                status.save()
    elif settings.config_sync_type == 2:
        master_url = settings.config_sync_master_url
        logger.info('start syncing configuration from ' + master_url)
        try:
            sync_status.objects.all().delete()
            sync_task = sync_status.objects.create(
                address=master_url,
                update_time=datetime.now(),
                status=1
            )

            r = requests.post(master_url + "/api/settings/sync_ack/", params={"access_key": settings.config_sync_access_key}, data=json.dumps({"status": 1}), headers={'Content-Type': 'application/json'}, timeout=3)
            if r.status_code != 200:
                logger.error('master [' + master_url + '], sync service is disabled or stop')
                sync_task.change_task_status(3)
                return False
            if bool(settings.config_sync_scope):
                logger.info('get config from ' + master_url + ', scope is only proxy')
                r = requests.get(master_url + "/api/settings/config/", params={"access_key": settings.config_sync_access_key, "scope": 0}, timeout=3)
            else:
                logger.info('get config from ' + master_url + ', scope is all')
                r = requests.get(master_url + "/api/settings/config/", params={"access_key": settings.config_sync_access_key, "scope": 1}, timeout=3)

            if r.status_code == 200:
                if import_config(r.json().get('context')):
                    requests.post(master_url + "/api/settings/sync_ack/", params={"access_key": settings.config_sync_access_key}, data=json.dumps({"status": 2}), headers={'Content-Type': 'application/json'}, timeout=3)
                    logger.info('task ' + master_url + ' sync finished')
                    sync_task.change_task_status(2)
                else:
                    requests.post(master_url + "/api/settings/sync_ack/", params={"access_key": settings.config_sync_access_key}, data=json.dumps({"status": 3}), headers={'Content-Type': 'application/json'}, timeout=3)
                    logger.error('task ' + master_url + ' sync failed, import config error.')
                    sync_task.change_task_status(3)
            else:
                requests.post(master_url + "/api/settings/sync_ack/", params={"access_key": settings.config_sync_access_key}, data=json.dumps({"status": 3}), headers={'Content-Type': 'application/json'}, timeout=3)
                logger.error('task ' + master_url + ' sync failed, get config error.')
                sync_task.change_task_status(3)

        except Exception as e:
            requests.post(master_url + "/api/settings/sync_ack/", params={"access_key": settings.config_sync_access_key}, data=json.dumps({"status": 3}), headers={'Content-Type': 'application/json'}, timeout=3)
            logger.error('task ' + master_url + ' sync failed')
            sync_task = sync_status.objects.get(address=master_url)
            if sync_task:
                sync_task.change_task_status(3)
    else:
        logger.info('syncing configuration disabled.')
        DjangoJobStore().remove_all_jobs()
        scheduler.remove_all_jobs()

