# Generated by Django 3.1.14 on 2022-02-21 23:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0022_auto_20220219_0948'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organizationteam',
            name='qualification',
        ),
    ]