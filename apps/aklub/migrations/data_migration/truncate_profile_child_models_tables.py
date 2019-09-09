# -*- coding: utf-8 -*-


def truncate_profile_child_models_tables(apps, schema_editor):
    """
    Truncate User/CompanyProfile model table

    handle error during migration:
    'django.db.utils.IntegrityError: column "profile_ptr_id" contains null value'
    """
    with schema_editor.connection.cursor() as cursor:
        for model in ['userprofile', 'companyprofile']:
            cursor.execute('TRUNCATE aklub_{}'.format(model))
