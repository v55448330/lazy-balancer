from django.db import models
import uuid

# Create your models here.
class system_settings(models.Model):
    access_key = models.CharField(max_length=64, null=True)
    config_sync_type = models.IntegerField(default=0)
    config_sync_access_key = models.CharField(max_length=64, null=True)
    config_sync_master_url = models.CharField(max_length=64, null=True)
    config_sync_interval = models.IntegerField(null=False, default=60)
    config_sync_scope = models.IntegerField(null=True)
    num_per_page = models.IntegerField(null=False, default=10)
    public_metric = models.BooleanField(null=False, default=False)

    class Meta:
       db_table = 't_settings'
    
    def update_access_key(self, disable=False):
        if disable:
            self.access_key = ''
        else:
            self.access_key = str(uuid.uuid4())
        self.save()

    def update_num_per_page(self, num_per_page):
        self.num_per_page = num_per_page
        self.save()

    def update_public_metric(self, public_metric):
        self.public_metric = public_metric
        self.save()


class sync_status(models.Model):
    update_time = models.DateTimeField(null=True)
    address = models.CharField(max_length=64, null=True)
    status = models.IntegerField(default=0)

    class Meta:
       db_table = 't_settings_sync_status'

    def change_task_status(self, status):
        self.status = status
        self.save()

