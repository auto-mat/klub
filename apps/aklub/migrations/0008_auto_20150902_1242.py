# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0007_auto_20150902_1223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='source',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='source_foreign',
            new_name='source',
        ),
    ]
