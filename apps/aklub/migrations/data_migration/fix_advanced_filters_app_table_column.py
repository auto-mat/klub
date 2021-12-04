# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db.utils import ProgrammingError

COLUMN_NAME = 'userprofile_id'


def forwards_func(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT EXISTS (SELECT 1
            FROM information_schema.columns
            WHERE table_name='advanced_filters_advancedfilter_users' AND column_name='{COLUMN_NAME}');
            """
        )
        column = cursor.fetchall()
        if column[0][0]:
            cursor.execute(
                ('ALTER TABLE advanced_filters_advancedfilter_users '
                 'RENAME {} TO {}_id').format(
                     COLUMN_NAME,
                     get_user_model()._meta.model_name,
                 ),
            )


def reverse_func(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            ('ALTER TABLE advanced_filters_advancedfilter_users '
             'RENAME {}_id TO {}').format(
                 get_user_model()._meta.model_name,
                 COLUMN_NAME,
             ),
        )
