# -*- coding: utf-8 -*-
from django.db import migrations, models
from django.conf import settings

from aklub.migrations.data_migration.old_user_profile_model_hack import Settings as settings


class Migration(migrations.Migration):

    dependencies = [
        ('helpdesk', '0013_email_box_local_dir_and_logging'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL,
                                       related_name='usersettings_helpdesk',
                                       on_delete=models.CASCADE),
        ),
    ]
