from __future__ import unicode_literals

from django.db import models

# Create your models here.
class upstream_config(models.Model):
    status = models.BooleanField(default=False)
    address = models.CharField(max_length=64,null=False)
    port = models.IntegerField(null=False)
    weight = models.IntegerField(null=False)

class proxy_config(models.Model):
    config_id = models.CharField(max_length=64,null=True)
    proxy_name = models.CharField(max_length=128,null=True)
    protocol = models.BooleanField(default=False,null=False)
    listen = models.IntegerField(null=False)
    server_name = models.CharField(max_length=128,null=True)
    access_log = models.CharField(max_length=128,null=True)
    error_log = models.CharField(max_length=128,null=True)
    balancer_type = models.CharField(max_length=64,null=True)
    http_check = models.BooleanField(default=False)
    gzip = models.BooleanField(default=False)
    description = models.TextField(null=True)

    ssl = models.BooleanField(default=False)
    ssl_http2 = models.BooleanField(default=False)
    ssl_redirect_https = models.BooleanField(default=False)
    ssl_cert = models.TextField(null=True)
    ssl_cert_path = models.CharField(max_length=128,null=True)
    ssl_key = models.TextField(null=True)
    ssl_key_path = models.CharField(max_length=128,null=True)

    custom_config= models.TextField(null=True)

    backend_protocol = models.CharField(max_length=64,null=True)
    backend_domain_toggle = models.BooleanField(default=False)
    backend_domain = models.CharField(max_length=128,null=True)
    host = models.CharField(max_length=64,null=True)
    status = models.BooleanField(default=False)
    update_time = models.FloatField(null=False)
    max_fails = models.IntegerField(default=5)
    fail_timeout = models.IntegerField(default=5)
    upstream_list = models.ManyToManyField(upstream_config)
