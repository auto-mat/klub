# Generated by Django 3.1.14 on 2024-04-04 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0028_auto_20240404_0810'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='date_to',
            field=models.DateTimeField(blank=True, db_column='date_to', null=True, verbose_name='Date and time to'),
        ),
    ]
