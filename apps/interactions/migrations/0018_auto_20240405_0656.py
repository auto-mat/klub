# Generated by Django 3.1.14 on 2024-04-05 04:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interactions', '0017_auto_20240405_0653'),
    ]

    operations = [
        migrations.CreateModel(
            name='InteractionStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(help_text='Status/progress of this communication', max_length=180, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Interaction status',
                'verbose_name_plural': 'Interaction statuses',
            },
        ),
        migrations.AddField(
            model_name='interactiontype',
            name='status_bool',
            field=models.BooleanField(default=False, help_text='Choose if status is visible in specific type of interaction.', verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='interaction',
            name='status',
            field=models.ForeignKey(blank=False, help_text='Status/progress of this communication', null=True, on_delete=django.db.models.deletion.SET_NULL, to='interactions.interactionstatus', verbose_name='Status'),
        ),
    ]
