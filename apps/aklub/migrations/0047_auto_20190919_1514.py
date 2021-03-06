# Generated by Django 2.2.4 on 2019-09-19 13:14

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import stdnumfield.models


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0046_auto_20190912_1254'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companyprofile',
            name='crn',
            field=stdnumfield.models.StdNumField(alphabets=[None], blank=True, default=None, error_messages={'stdnum_format': 'IČO není zadáno ve správném formátu. Zkontrolujte že číslo má osm číslic a případně ho doplňte nulami zleva.'}, formats=['cz.dic'], help_text='only for Czech companies', null=True, validators=[django.core.validators.RegexValidator('^[0-9]*$', 'IČO musí být číslo')], verbose_name='IČO'),
        ),
        migrations.AlterField(
            model_name='companyprofile',
            name='tin',
            field=stdnumfield.models.StdNumField(alphabets=[None], blank=True, default=None, formats=['eu.vat'], help_text='Czech and European companies, must be in valid formate', null=True, verbose_name='DIČ'),
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='send_to_users',
            field=models.ManyToManyField(blank=True, help_text='All users who should receive the communication', limit_choices_to={'is_active': 'True', 'preference__send_mailing_lists': 'True'}, to=settings.AUTH_USER_MODEL, verbose_name='send to users'),
        ),
    ]
