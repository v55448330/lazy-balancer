# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proxy', '0011_proxy_config_check_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='proxy_config',
            name='host',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
