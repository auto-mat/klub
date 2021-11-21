# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db.utils import ProgrammingError

COLUMN_NAME = 'userprofile_id'


def forwards_func(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            ('ALTER TABLE advanced_filters_advancedfilter_users '
             'RENAME {}_id TO {}').format(
                 get_user_model()._meta.model_name,
                 COLUMN_NAME
             ),
        )


def reverse_func(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            ('ALTER TABLE advanced_filters_advancedfilter_users '
             'RENAME {} TO {}_id').format(
                 COLUMN_NAME,
                 get_user_model()._meta.model_name,
             ),
        )
