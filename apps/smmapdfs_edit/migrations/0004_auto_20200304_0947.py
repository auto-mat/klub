# Generated by Django 2.2.10 on 2020-03-04 08:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('smmapdfs_edit', '0003_delete_pdfsandwichfontconnector'),
    ]

    operations = [
        migrations.AddField(
            model_name='pdfsandwichtypeconnector',
            name='profile_type',
            field=models.CharField(choices=[('company_profile', 'Company profile'), ('user_profile', 'User profile')], default='user_profile', max_length=50),
        ),
        migrations.AlterField(
            model_name='pdfsandwichemailconnector',
            name='administrative_unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit'),
        ),
        migrations.AlterField(
            model_name='pdfsandwichtypeconnector',
            name='administrative_unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit'),
        ),
    ]