# Generated by Django 2.2.8 on 2020-01-02 13:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0058_taxconfirmation_administrative_unit'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='taxconfirmation',
            unique_together=set(),
        ),
    ]
