# Generated by Django 2.2.20 on 2021-04-29 16:35

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interactions', '0012_auto_20210211_1311'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interactiontype',
            name='slug',
            field=autoslug.fields.AutoSlugField(blank=True, editable=True, help_text='Identifier of the Interaction Type', max_length=100, null=True, populate_from='name', verbose_name='Slug'),
        ),
    ]
