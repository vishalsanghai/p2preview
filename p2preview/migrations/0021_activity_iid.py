# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-25 16:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('p2preview', '0020_auto_20171025_1405'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='iId',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='p2preview.Instrutor'),
            preserve_default=False,
        ),
    ]
