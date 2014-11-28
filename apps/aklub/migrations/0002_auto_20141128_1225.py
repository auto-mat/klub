# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountstatements',
            name='import_date',
            field=models.DateField(auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='automaticcommunication',
            name='template',
            field=models.TextField(help_text='Template can contain variable substitutions like addressment, name, variable symbol etc.', max_length=50000, verbose_name='Template'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='automaticcommunication',
            name='template_en',
            field=models.TextField(max_length=50000, null=True, verbose_name='English template', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='communication',
            name='summary',
            field=models.TextField(help_text='Text or summary of this communication', max_length=50000, verbose_name='Text'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='template',
            field=models.TextField(help_text='Template can contain variable substitutions like addressment, name, variable symbol etc.', max_length=50000, null=True, verbose_name='Template', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='template_en',
            field=models.TextField(max_length=50000, null=True, verbose_name='English template', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='recruiter',
            name='registered',
            field=models.DateField(default=datetime.datetime(2014, 11, 28, 12, 25, 33, 814531), verbose_name='Registered'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='registered_support',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 28, 12, 25, 33, 818643), help_text='When did this user register to support us', verbose_name='Registered support', blank=True),
            preserve_default=True,
        ),
    ]
