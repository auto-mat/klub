# Generated by Django 2.2.18 on 2021-02-11 11:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0093_auto_20210211_1250'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'managed': False, 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AlterModelOptions(
            name='eventtype',
            options={'managed': False, 'verbose_name': 'Event type', 'verbose_name_plural': 'Event types'},
        ),
    ]
