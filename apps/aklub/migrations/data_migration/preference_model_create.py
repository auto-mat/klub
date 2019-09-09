# -*- coding: utf-8 -*-

from .old_user_profile_model_hack import Settings as settings

def preference_model_create(apps, schema_editor):
    profile_model = apps.get_model('aklub', settings.AUTH_USER_MODEL.split('.')[1])
    preference_model = apps.get_model('aklub', 'Preference')
    for user in profile_model.objects.all():
        for unit in user.administrative_units.all():
            preference_model.objects.get_or_create(
                user=user,
                administrative_unit=unit,
            )
