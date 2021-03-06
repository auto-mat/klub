# Generated by Django 2.1.7 on 2019-03-20 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0018_auto_20190227_1130'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='Bank account note'),
        ),
        migrations.AddField(
            model_name='donorpaymentchannel',
            name='user_bank_account',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='userbankaccounts', to='aklub.BankAccount'),
        ),
    ]
