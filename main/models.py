from django.db import models

# Create your models here.
class main_config(models.Model):
    config_id = models.CharField(max_length=64,null=True)
    worker_processes = models.IntegerField(null=False)
    worker_connections = models.IntegerField(null=False)
    keepalive_timeout = models.IntegerField(null=False)
    client_max_body_size = models.IntegerField(null=False)
    ignore_invalid_headers = models.BooleanField(default=False)
    http_log_format = models.TextField(null=True)
    stream_log_format = models.TextField(null=True)
    access_log = models.CharField(max_length=128,null=True)
    error_log = models.CharField(max_length=128,null=True)
    update_time = models.FloatField(null=False)

    class Meta:
       db_table = 't_main_config'







# Create your models here.
