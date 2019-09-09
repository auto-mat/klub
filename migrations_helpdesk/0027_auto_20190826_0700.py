# Generated by Django 2.2.4 on 2019-08-26 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helpdesk', '0026_kbitem_attachments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='followupattachment',
            name='filename',
            field=models.CharField(blank=True, max_length=1000, verbose_name='Filename'),
        ),
        migrations.AlterField(
            model_name='followupattachment',
            name='mime_type',
            field=models.CharField(blank=True, max_length=255, verbose_name='MIME Type'),
        ),
        migrations.AlterField(
            model_name='followupattachment',
            name='size',
            field=models.IntegerField(blank=True, help_text='Size of this file in bytes', verbose_name='Size'),
        ),
        migrations.AlterField(
            model_name='kbiattachment',
            name='filename',
            field=models.CharField(blank=True, max_length=1000, verbose_name='Filename'),
        ),
        migrations.AlterField(
            model_name='kbiattachment',
            name='mime_type',
            field=models.CharField(blank=True, max_length=255, verbose_name='MIME Type'),
        ),
        migrations.AlterField(
            model_name='kbiattachment',
            name='size',
            field=models.IntegerField(blank=True, help_text='Size of this file in bytes', verbose_name='Size'),
        ),
        migrations.AlterField(
            model_name='queue',
            name='enable_notifications_on_email_events',
            field=models.BooleanField(blank=True, default=False, help_text='When an email arrives to either create a ticket or to interact with an existing discussion. Should email notifications be sent ? Note: the new_ticket_cc and updated_ticket_cc work independently of this feature', verbose_name='Notify contacts when email updates arrive'),
        ),
    ]
