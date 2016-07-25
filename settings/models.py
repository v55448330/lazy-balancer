from __future__ import unicode_literals

from django.db import models

# Create your models here.

class system_settings(models.Model):
    internal_nic = models.CharField(max_length=64,null=True)
