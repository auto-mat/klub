# Generated by Django 2.2.19 on 2021-04-16 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0099_delete_userincampaign'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donorpaymentchannel',
            name='VS',
            field=models.CharField(blank=True, help_text='Variable symbol', max_length=30, verbose_name='VS'),
        ),
    ]