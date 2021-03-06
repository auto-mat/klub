# Generated by Django 2.2.4 on 2019-09-12 10:54

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0045_auto_20190910_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companyprofile',
            name='crn',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Company Registration Number'),
        ),
        migrations.AlterField(
            model_name='companyprofile',
            name='tin',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Tax Identification Number'),
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='send_to_users',
            field=models.ManyToManyField(blank=True, help_text='All users who should receive the communication', limit_choices_to={'is_active': 'True', 'preference__send_mailing_lists': 'True'}, to=settings.AUTH_USER_MODEL, verbose_name='send to users'),
        ),
    ]
