# Generated by Django 2.2.9 on 2020-02-06 13:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0072_auto_20200206_1153'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='automaticcommunication',
            name='method',
        ),
        migrations.RemoveField(
            model_name='masscommunication',
            name='method',
        ),
    ]
