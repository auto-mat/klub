# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model

COLUMN_NAME = 'userprofile_id'


def forwards_func(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        sql = "ALTER TABLE advanced_filters_advancedfilter_users " \
            "RENAME {} TO {}_id;".format(COLUMN_NAME, get_user_model()._meta.model_name)
        cursor.execute(sql)

    
def reverse_func(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        sql = "ALTER TABLE advanced_filters_advancedfilter_users " \
            "RENAME {}_id TO {};".format(get_user_model()._meta.model_name, COLUMN_NAME)
        cursor.execute(sql)
