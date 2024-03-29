# Generated by Django 3.1.14 on 2024-03-26 19:22

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0024_auto_20230327_1228'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['tn_order'], 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AddField(
            model_name='event',
            name='tn_ancestors_count',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Ancestors count'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_ancestors_pks',
            field=models.TextField(blank=True, default='', editable=False, verbose_name='Ancestors pks'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_children_count',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Children count'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_children_pks',
            field=models.TextField(blank=True, default='', editable=False, verbose_name='Children pks'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_depth',
            field=models.PositiveIntegerField(default=0, editable=False, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)], verbose_name='Depth'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_descendants_count',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Descendants count'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_descendants_pks',
            field=models.TextField(blank=True, default='', editable=False, verbose_name='Descendants pks'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_index',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Index'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_level',
            field=models.PositiveIntegerField(default=1, editable=False, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)], verbose_name='Level'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_order',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tn_children', to='events.event', verbose_name='Parent'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_priority',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(9999)], verbose_name='Priority'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_siblings_count',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Siblings count'),
        ),
        migrations.AddField(
            model_name='event',
            name='tn_siblings_pks',
            field=models.TextField(blank=True, default='', editable=False, verbose_name='Siblings pks'),
        ),
    ]
