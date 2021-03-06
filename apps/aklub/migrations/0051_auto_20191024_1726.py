# Generated by Django 2.2.6 on 2019-10-15 15:26

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('aklub', '0050_auto_20191023_154700'),
    ]
    operations = [
        migrations.CreateModel(
            name='MoneyAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True, null=True, verbose_name='Bank account note')),
                ('administrative_unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit', verbose_name='administrative unit')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_aklub.moneyaccount_set+', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
        ),
        migrations.RemoveField(
            model_name='bankaccount',
            name='administrative_unit',
        ),
        migrations.RemoveField(
            model_name='bankaccount',
            name='id',
        ),
        migrations.RemoveField(
            model_name='bankaccount',
            name='note',
        ),
        migrations.AlterField(
            model_name='accountstatements',
            name='type',
            field=models.CharField(choices=[('account', 'Account statement - Fio Banka'), ('account_cs', 'Account statement - Česká spořitelna'), ('account_kb', 'Account statement - Komerční Banka'), ('account_csob', 'Account statement - ČSOB'), ('account_sberbank', 'Account statement - Sberbank'), ('darujme', 'Darujme.cz')], max_length=20),
        ),
        migrations.AddField(
            model_name='bankaccount',
            name='moneyaccount_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='aklub.MoneyAccount'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='donorpaymentchannel',
            name='money_account',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='moneyaccounts', to='aklub.MoneyAccount'),
        ),
        migrations.AlterUniqueTogether(
            name='donorpaymentchannel',
            unique_together={('VS', 'money_account')},
        ),
        migrations.CreateModel(
            name='ApiAccount',
            fields=[
                ('moneyaccount_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='aklub.MoneyAccount')),
                ('project_name', models.CharField(blank=True, default=None, max_length=100, null=True, unique=True, verbose_name='Name')),
                ('project_id', models.IntegerField(blank=True, default=None, null=True, verbose_name='project ID')),
                ('api_id', models.IntegerField(blank=True, default=None, null=True, verbose_name='API ID')),
                ('api_secret', models.CharField(blank=True, default=None, max_length=100, null=True, verbose_name='API secret')),
                ('event', models.ForeignKey(blank=True, help_text='Event', null=True, on_delete=django.db.models.deletion.SET_NULL, to='aklub.Event', verbose_name='Event')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('aklub.moneyaccount',),
        ),
        migrations.RemoveField(
            model_name='donorpaymentchannel',
            name='bank_account',
        ),
    ]
