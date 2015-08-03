# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def make_terminal_conditions_reverse(apps, schema_editor):
    pass

def make_terminal_conditions(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Condition = apps.get_model("aklub", "Condition")
    TerminalCondition = apps.get_model("aklub", "TerminalCondition")
    for condition in Condition.objects.all():
        if condition.variable:
            tc = TerminalCondition(
                variable=condition.variable,
                value=condition.value,
                operation=condition.operation,
                condition=condition,
            )
            tc.save()
            condition.operation = "and"
            condition.save()

class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0006_auto_20150731_1454'),
    ]


    operations = [
        migrations.RunPython(make_terminal_conditions, reverse_code=make_terminal_conditions_reverse),
    ]
