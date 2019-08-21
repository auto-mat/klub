# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model


def preference_model_create(apps, schema_editor):
    profile_model = get_user_model()  # get Profile model this way, check the commit d3180343ac0a8a3ad9b1dad401ddf6e802fafdc4
    preference_model = apps.get_model('aklub', 'Preference')
    for user in profile_model.objects.all():
        for unit in user.administrative_units.all():
            preference_model.objects.get_or_create(
                user=user,
                administrative_unit=unit,
            )

