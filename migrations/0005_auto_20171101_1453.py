# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-01 03:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20171101_1436'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Title', models.CharField(max_length=250)),
                ('Unit', models.CharField(max_length=250)),
                ('Quantity', models.FloatField()),
            ],
        ),
        migrations.RemoveField(
            model_name='ingredent',
            name='Recipe',
        ),
        migrations.DeleteModel(
            name='Ingredent',
        ),
        migrations.AddField(
            model_name='recipe',
            name='Ingredients',
            field=models.ManyToManyField(to='recipes.Ingredient'),
        ),
    ]
