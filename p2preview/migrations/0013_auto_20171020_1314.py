# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-20 13:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('p2preview', '0012_auto_20171020_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='response',
            name='comment',
            field=models.CharField(blank=True, default='', max_length=30, null=True),
        ),
    ]
