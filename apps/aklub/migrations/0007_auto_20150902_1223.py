# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def migrate_source(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    SOURCE = {
        'web': "Web form",
        'dpnk': "DPNK campaign",
        'lead-dpnk': "DPNK campaign - lead",
        'direct-dialogue-partial-form': "Direct dialogue -- partial form (not automatic in bank)",
        'direct-dialogue-full-form': "Direct dialogue -- full form (automatic in bank)",
        'direct-dialogue-event': "Direct dialogue -- event",
        'telephone-call': "Telephonic call",
        'personal': 'Personal recommendation',
        'darujme': 'Darujme.cz',
        'other': 'Another form of contact'}

    Source = apps.get_model("aklub", "Source")
    User = apps.get_model("aklub", "User")
    for user in User.objects.all():
        source_char = user.source
        source_description = SOURCE[source_char]
        source, created = Source.objects.get_or_create(slug=source_char, defaults={'name': source_description})
        user.source_foreign = source
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0006_auto_20150902_1230'),
    ]

    operations = [
        migrations.RunPython(migrate_source),
    ]
