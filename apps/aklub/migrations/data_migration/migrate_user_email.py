# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model


def migrate_user_email(apps, schema_editor):
    profile_model = get_user_model()
    with schema_editor.connection.cursor() as cursor:
        for user in profile_model.objects.all().only('email', 'id'):
            cursor.execute(
                "INSERT INTO aklub_profileemail (email, user_id, is_primary) VALUES (%s, %s, %s)",
                [user.email, user.id, True]
            )
