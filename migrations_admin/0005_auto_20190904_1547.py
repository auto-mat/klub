# Generated by Django 2.2.4 on 2019-09-04 13:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from aklub.migrations.data_migration.old_user_profile_model_hack import Settings as settings


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0004_auto_20190826_2034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logentry',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]