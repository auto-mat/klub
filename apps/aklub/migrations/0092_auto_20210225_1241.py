# Generated by Django 2.2.18 on 2021-02-25 11:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0091_auto_20201111_1403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donorpaymentchannel',
            name='event',
            field=models.ForeignKey(help_text='Event', on_delete=django.db.models.deletion.CASCADE, to='aklub.Event', verbose_name='Event'),
        ),
    ]
