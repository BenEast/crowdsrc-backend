# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-15 16:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdsrc', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='body',
            field=models.TextField(max_length=2000),
        ),
    ]