# -*- coding: utf-8 -*-

USER_PROFILE_MODEL_DATA = []


def dict_fetch_all(cursor):
    """ Return all rows from a cursor as a dict """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_user_model_data(apps, schema_editor):
    global USER_PROFILE_MODEL_DATA
    content_type_model = apps.get_model('contenttypes', 'contenttype')
    if content_type_model.objects.count() > 1:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                ''.join(
                    [
                        "SELECT id, age_group, birth_day,",
                        " birth_month, title_after, title_before FROM",
                        " aklub_profile WHERE polymorphic_ctype_id = %s",
                    ]
                ),
                [
                    content_type_model.objects.get(app_label='aklub', model='userprofile').id
                ]
            )
            USER_PROFILE_MODEL_DATA = dict_fetch_all(cursor)


def set_user_model_data(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for user in USER_PROFILE_MODEL_DATA:
            cursor.execute(
                ''.join(
                    [
                        "UPDATE aklub_userprofile SET",
                        " age_group=%s, birth_day=%s,",
                        " birth_month=%s, title_after=%s, title_before=%s",
                        " WHERE profile_ptr_id=%s",
                    ]
                ),
                [
                    user['age_group'],
                    user['birth_day'],
                    user['birth_month'],
                    user['title_after'],
                    user['title_before'],
                    user['id'],
                ]
            )
