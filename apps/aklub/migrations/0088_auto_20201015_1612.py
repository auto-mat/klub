# Generated by Django 2.2.16 on 2020-10-15 14:12

from django.db import migrations


class Migration(migrations.Migration):

    def add_interaction_type(apps, schema_editor):
        InteractionType = apps.get_model('interactions', 'InteractionType')
        InteractionCategory= apps.get_model('interactions', 'InteractionCategory')
        int_cat, _ = InteractionCategory.objects.get_or_create(category='profile actions')
        InteractionType.objects.get_or_create(name='Administrative unit was added', slug='administrative_unit_added', category=int_cat)
        InteractionType.objects.get_or_create(name='Administrative unit was removed', slug='administrative_unit_removed', category=int_cat)


    dependencies = [
        ('aklub', '0087_auto_20200918_1159'),
    ]

    operations = [
        migrations.RunPython(add_interaction_type, reverse_code=migrations.RunPython.noop),
    ]
