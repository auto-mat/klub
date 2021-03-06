# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-07 18:17
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.admin.models
from django.db import migrations, models
import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone

from aklub.migrations.data_migration.old_user_profile_model_hack import Settings as settings

# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# migrations_admin.0006_auto_20171021_0957

class Migration(migrations.Migration):

    replaces = [('admin', '0001_initial'), ('admin', '0002_logentry_remove_auto_add'), ('admin', '0003_auto_20171018_1022'), ('admin', '0004_auto_20171018_1023'), ('admin', '0005_auto_20171021_0910'), ('admin', '0006_auto_20171021_0957'), ('admin', '0007_auto_20171021_0959')]

    initial = True

    dependencies = [
        ('contenttypes', '__first__'),
        ('aklub', '0045_auto_20171020_1506'),
        ('auth', '__first__'),
        ('aklub', '0046_auto_20171020_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_time', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='action time')),
                ('object_id', models.TextField(blank=True, null=True, verbose_name='object id')),
                ('object_repr', models.CharField(max_length=200, verbose_name='object repr')),
                ('action_flag', models.PositiveSmallIntegerField(verbose_name='action flag')),
                ('change_message', models.TextField(blank=True, verbose_name='change message')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.ContentType', verbose_name='content type')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name_plural': 'log entries',
                'db_table': 'django_admin_log',
                'ordering': ('-action_time',),
                'verbose_name': 'log entry',
            },
            managers=[
                ('objects', django.contrib.admin.models.LogEntryManager()),
            ],
        ),
    ]
