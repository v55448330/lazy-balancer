from __future__ import unicode_literals

from django.db import models
from OpenSSL import crypto
from dateutil import parser

# Create your models here.
class upstream_config(models.Model):
    status = models.BooleanField(default=False)
    address = models.CharField(max_length=64,null=False)
    port = models.IntegerField(null=False)
    weight = models.IntegerField(null=False)
    class Meta:
       db_table = 't_proxy_upstream_config'

class proxy_config(models.Model):
    config_id = models.CharField(max_length=64,null=True)
    proxy_name = models.CharField(max_length=128,null=True)
    protocol = models.BooleanField(default=False,null=False)
    listen = models.IntegerField(null=False)
    ipv6 = models.BooleanField(default=False,null=False)
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
    backend_dynamic_domain = models.BooleanField(default=False)
    backend_domain = models.CharField(max_length=128,null=True)
    host = models.CharField(max_length=64,null=True)
    status = models.BooleanField(default=False)
    update_time = models.FloatField(null=False)
    max_fails = models.IntegerField(default=5)
    fail_timeout = models.IntegerField(default=5)
    upstream_list = models.ManyToManyField(upstream_config)

    class Meta:
       db_table = 't_proxy_config'
    
    def update_cert(self, ssl_cert, ssl_key):
        try:
            crypto.load_certificate(crypto.FILETYPE_PEM, ssl_cert)
            self.ssl_cert = ssl_cert
            self.ssl_key = ssl_key
            self.save(update_fields=['ssl_cert', 'ssl_key', 'update_time'])
        except:
            return False
        return True

    def get_cert_status(self):
        # print(cert_file_path)
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, self.ssl_cert)
        cert_issuer = cert.get_issuer()
        cert_info = {
            'subject': cert.get_subject().CN,
            'issuer' : "%s/%s/%s" % (cert_issuer.C,cert_issuer.O,cert_issuer.CN),
            'datetime_struct' : parser.parse(cert.get_notAfter().decode("UTF-8")).strftime('%Y-%m-%d %H:%M:%S'),
            'has_expired' : cert.has_expired()
        }
        return cert_info
    
    def get_upstream_status(self, status_data):
        status=[]
        for s in status_data:
            if s.get('upstream') == self.config_id:
                status.append(s)

        return status
