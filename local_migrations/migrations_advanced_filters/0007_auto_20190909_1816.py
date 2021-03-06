# Generated by Django 2.2.4 on 2019-09-09 16:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from aklub.migrations.data_migration.old_user_profile_model_hack import Settings as settings


class Migration(migrations.Migration):

    dependencies = [
        ('advanced_filters', '0006_auto_20190909_1723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advancedfilter',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_advanced_filters', to=settings.AUTH_USER_MODEL, verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='advancedfilter',
            name='users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='Users'),
        ),
    ]
