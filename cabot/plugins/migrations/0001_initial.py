# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-12 10:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import picklefield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertPluginUserData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=128)),
                ('value', picklefield.fields.PickledObjectField(editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='PluginModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=256, unique=True)),
                ('timestamp_installed', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AlertPluginModel',
            fields=[
                ('pluginmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='plugins.PluginModel')),
            ],
            options={
                'abstract': False,
            },
            bases=('plugins.pluginmodel',),
        ),
        migrations.CreateModel(
            name='StatusCheckPluginModel',
            fields=[
                ('pluginmodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='plugins.PluginModel')),
            ],
            options={
                'abstract': False,
            },
            bases=('plugins.pluginmodel',),
        ),
        migrations.AddField(
            model_name='pluginmodel',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_plugins.pluginmodel_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='alertpluginuserdata',
            name='plugin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plugins.PluginModel'),
        ),
        migrations.AddField(
            model_name='alertpluginuserdata',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='alertpluginuserdata',
            unique_together=set([('user', 'key', 'plugin')]),
        ),
    ]
