# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-19 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20171105_1831'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='Title',
            field=models.CharField(max_length=250, unique=True),
        ),
    ]
