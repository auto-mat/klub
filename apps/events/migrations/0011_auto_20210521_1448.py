# Generated by Django 2.2.20 on 2021-05-21 12:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_auto_20210519_1211'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organizationteam',
            name='can_be_contacted',
        ),
        migrations.AddField(
            model_name='event',
            name='contact_person_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Contact person email address'),
        ),
        migrations.AddField(
            model_name='event',
            name='contact_person_name',
            field=models.CharField(blank=True, max_length=128, verbose_name='Contact person name'),
        ),
        migrations.AddField(
            model_name='event',
            name='contact_person_telephone',
            field=models.CharField(blank=True, max_length=100, validators=[django.core.validators.RegexValidator('^\\+?(42(0|1){1})?\\s?\\d{3}\\s?\\d{3}\\s?\\d{3}$', 'Telephone must consist of numbers, spaces and + sign or maximum number count is higher.')], verbose_name='Contact person telephone number'),
        ),
    ]
