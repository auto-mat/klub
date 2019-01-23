# Generated by Django 2.1.5 on 2019-01-22 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0014_auto_20181211_1624'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='donor_payment_channel',
        ),
        migrations.AddField(
            model_name='donorpaymentchannel',
            name='event',
            field=models.ManyToManyField(blank=True, related_name='donorevents', to='aklub.Event'),
        ),
    ]
