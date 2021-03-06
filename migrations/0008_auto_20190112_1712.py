# Generated by Django 2.1.4 on 2019-01-12 06:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_auto_20180419_2041'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredient',
            name='Recipe',
        ),
        migrations.AddField(
            model_name='recipe',
            name='Ingredients',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='Category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='recipes.Category'),
        ),
    ]
