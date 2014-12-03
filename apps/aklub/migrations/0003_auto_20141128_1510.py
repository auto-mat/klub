# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0002_auto_20141128_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountstatements',
            name='type',
            field=models.CharField(default=b'account', max_length=20, choices=[(b'account', 'Account statement'), (b'darujme', b'Darujme.cz')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='payment',
            name='type',
            field=models.CharField(blank=True, help_text='Type of payment', max_length=200, verbose_name='Type', choices=[(b'bank-transfer', 'Bank transfer'), (b'cash', 'In cash'), (b'expected', 'Expected payment'), (b'darujme', b'Darujme.cz')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='recruiter',
            name='registered',
            field=models.DateField(default=datetime.datetime(2014, 11, 28, 15, 10, 30, 185856), verbose_name='Registered'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='registered_support',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 28, 15, 10, 30, 188566), help_text='When did this user register to support us', verbose_name='Registered support', blank=True),
            preserve_default=True,
        ),
    ]
