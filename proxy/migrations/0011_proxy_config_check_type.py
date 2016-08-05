# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proxy', '0010_auto_20160718_0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='proxy_config',
            name='check_type',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
