# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-01 07:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('p2preview', '0009_auto_20171001_0702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='fileURL',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='rubric',
            name='name',
            field=models.CharField(default='', max_length=30),
        ),
    ]
