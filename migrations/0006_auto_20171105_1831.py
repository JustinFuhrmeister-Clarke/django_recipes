# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-05 07:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_auto_20171101_1453'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='Ingredients',
        ),
        migrations.AddField(
            model_name='ingredient',
            name='Recipe',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='recipes.Recipe'),
            preserve_default=False,
        ),
    ]
