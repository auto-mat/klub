# Generated by Django 2.2.2 on 2019-07-15 11:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0030_auto_20190627_1624'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountstatements',
            name='administrative_unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit', verbose_name='administrative unit'),
        ),
    ]
