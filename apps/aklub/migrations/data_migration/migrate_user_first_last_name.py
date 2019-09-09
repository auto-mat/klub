# -*- coding: utf-8 -*-

from .migrate_user_profile_data import dict_fetch_all

USER_PROFILE_MODEL_DATA = []
COMPANY_PROFILE_MODEL_DATA = []


def get_user_model_data(apps, schema_editor):
    global USER_PROFILE_MODEL_DATA
    global COMPANY_PROFILE_MODEL_DATA
    content_type_model = apps.get_model('contenttypes', 'contenttype')
    if content_type_model.objects.count() > 1:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                ''.join(
                    [
                        "SELECT id, first_name, last_name FROM",
                        " aklub_profile WHERE polymorphic_ctype_id = %s",
                    ]
                ),
                [
                    content_type_model.objects.get(app_label='aklub', model='userprofile').id
                ]
            )
            USER_PROFILE_MODEL_DATA = dict_fetch_all(cursor)

            cursor.execute(
                ''.join(
                    [
                        "SELECT id, first_name, last_name FROM",
                        " aklub_profile WHERE polymorphic_ctype_id = %s",
                    ]
                ),
                [
                    content_type_model.objects.get(app_label='aklub', model='companyprofile').id
                ]
            )
            COMPANY_PROFILE_MODEL_DATA = dict_fetch_all(cursor)


def set_user_model_data(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for user in USER_PROFILE_MODEL_DATA:
            cursor.execute(
                ''.join(
                    [
                        "UPDATE aklub_userprofile SET",
                        " first_name=%s, last_name=%s",
                        " WHERE profile_ptr_id=%s",
                    ]
                ),
                [
                    user['first_name'],
                    user['last_name'],
                    user['id'],
                ]
            )
        for user in COMPANY_PROFILE_MODEL_DATA:
            cursor.execute(
                ''.join(
                    [
                        "UPDATE aklub_companyprofile SET",
                        " name=%s",
                        " WHERE profile_ptr_id=%s",
                    ]
                ),
                [
                    user['first_name'] + ' ' + user['last_name'],
                    user['id'],
                ]
            )
