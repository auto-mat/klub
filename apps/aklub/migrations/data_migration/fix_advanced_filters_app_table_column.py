# -*- coding: utf-8 -*-

COLUMN_NAME = 'userprofile_id'


def forwards_func(apps, schema_editor):
    migrations.RunSQL("ALTER TABLE advanced_filters_advancedfilter_users " \
                      "RENAME {} TO {}_id".format(COLUMN_NAME, get_user_model()._meta.model_name)),

    
def reverse_func(apps, schema_editor):
    migrations.RunSQL("ALTER TABLE advanced_filters_advancedfilter_users " \
                      "RENAME {}_id TO {}".format(get_user_model()._meta.model_name),
                      COLUMN_NAME),
