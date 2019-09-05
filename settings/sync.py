from .models import system_settings, sync_status
from .views import import_config
import requests
import logging
logger = logging.getLogger('django')

def sync_config():
    settings = system_settings.objects.last()
    if settings.config_sync_type == 2:
        master_url = settings.config_sync_master_url
        logger.info('start syncing configuration from ' + master_url)
        try:
            sync_status.objects.all().delete()
            sync_task = sync_status.objects.create(
                address=master_url,
                update_time=datetime.now(),
                status=1
            )

            if bool(settings.config_sync_scope):
                logger.info('get config from ' + master_url + ', scope is only proxy')
                r = requests.get("http://httpbin.org/get", params={ "access_key": settings.config_sync_access_key, "scope": 0 }, timeout=3)
            else:
                logger.info('get config from ' + master_url + ', scope is all')
                r = requests.get("http://httpbin.org/get", params={ "access_key": settings.config_sync_access_key, "scope": 1 }, timeout=3)
            
            if import_config(r.json()):
                logger.error('task ' + master_url + ' sync finished')
                sync_task.change_task_status(2)
            else:
                logger.error('task ' + master_url + ' sync failed')
                sync_task.change_task_status(3)

        except Exception,e:
            logger.error('task ' + master_url + ' sync failed')
            sync_task = sync_status.objects.get(address=master_url)
            if sync_task:
                sync_task.change_task_status(3)
        

        



