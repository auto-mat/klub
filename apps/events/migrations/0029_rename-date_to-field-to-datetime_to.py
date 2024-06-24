# Generated by Django 3.1.14 on 2024-04-04 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('events', '0029_auto_20240404_0912'), ('events', '0030_auto_20240404_0915')]

    dependencies = [
        ('events', '0028_auto_20240404_0810'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='date_to',
            new_name='datetime_to',
        ),
        migrations.AlterField(
            model_name='event',
            name='datetime_to',
            field=models.DateTimeField(blank=True, db_column='date_to', null=True, verbose_name='Date and time to'),
        ),
    ]