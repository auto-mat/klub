# -*- coding: utf-8 -*-

from  django.contrib.contenttypes.models import ContentType

ONETOONE_USER_PROFILE_MODEL_DATA = []
USER_PROFILE_MODEL_DATA = []


def get_user_model_data(apps, schema_editor):
    """Copy exist user model data before change model name/structure
    old model UserProfile -> new model Profile
    """
    user_profile_model = apps.get_model('aklub', 'UserProfile')
    global USER_PROFILE_MODEL_DATA
    global SPECIFIC_USER_PROFILE_DATA
    if ContentType.objects.count() > 0:
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM aklub_userprofile")
            content_type_id = ContentType.objects.get(model=user_profile_model._meta.model_name).id        
            rows = [list(row) + [content_type_id] for row in cursor.fetchall()]
            columns = [col[0] for col in cursor.description]
            columns.append('polymorphic_ctype_id')
            USER_PROFILE_MODEL_DATA = [
                dict(zip(columns, row)) for row in rows
            ]
            for user in USER_PROFILE_MODEL_DATA:
                ONETOONE_USER_PROFILE_MODEL_DATA.append(
                    {
                        'user_id': user['id'],
                        'sex': user.pop('sex'),

                    }
                )

            
def set_user_model_data(apps, schema_editor):
    """Fullfill new model Profile with old UserProfile model data"""
    profile_model = apps.get_model('aklub', 'Profile')
    user_profile_model = apps.get_model('aklub', 'UserProfile')
    for user in USER_PROFILE_MODEL_DATA:
        new_model = profile_model(**user)
        new_model.save()
    # Handle OneToOne relationship
    with schema_editor.connection.cursor() as cursor:
        for extend_user_data in ONETOONE_USER_PROFILE_MODEL_DATA:
            cursor.execute("INSERT INTO aklub_userprofile (profile_ptr_id, sex) VALUES(%s, %s)",
                           [extend_user_data['user_id'], extend_user_data['sex']])
