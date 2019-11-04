from __future__ import unicode_literals

from django.db import models

# Create your models here.

class system_settings(models.Model):
    config_sync_type = models.IntegerField(default=0)
    config_sync_access_key = models.CharField(max_length=64,null=True)
    config_sync_master_url = models.CharField(max_length=64,null=True)
    config_sync_interval = models.IntegerField(null=False,default=60)
    config_sync_scope = models.IntegerField(null=True)

class sync_status(models.Model):
    update_time = models.DateTimeField(null=True)
    address = models.CharField(max_length=64,null=True)
    status = models.IntegerField(default=0)

    def change_task_status(self, status):
        self.status = status
        self.save()

