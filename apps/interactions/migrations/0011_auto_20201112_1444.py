# Generated by Django 2.2.16 on 2020-11-12 13:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('aklub', '0091_auto_20201111_1403'),
        ('interactions', '0010_auto_20201209_1107'),
    ]

    operations = [
        migrations.AddField(
            model_name='petitionsignature',
            name='administrative_unit',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit', verbose_name='Administrative unit'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='petitionsignature',
            unique_together={('user', 'event')},
        ),
        migrations.RemoveField(
            model_name='petitionsignature',
            name='date',
        ),
    ]
