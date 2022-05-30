# Generated by Django 3.1.14 on 2022-01-16 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_auto_20220117_0051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='program',
            field=models.CharField(blank=True, choices=[('zmj', 'Zažít město jinak'), ('dpnk', 'Do práce na Kole'), ('lab', 'LAB')], default='', max_length=128, verbose_name='Program'),
        ),
    ]