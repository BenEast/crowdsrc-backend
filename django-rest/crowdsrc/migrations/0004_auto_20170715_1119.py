# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-15 16:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdsrc', '0003_auto_20170715_1101'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='message',
        ),
        migrations.AddField(
            model_name='comment',
            name='comment_body',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
