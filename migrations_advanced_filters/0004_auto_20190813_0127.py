# Generated by Django 2.2.4 on 2019-08-12 23:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('advanced_filters', '0003_auto_20180610_0718'),
        ('aklub', '0002_auto_20171109_1518_squashed_0038_auto_20190807_0754'),
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