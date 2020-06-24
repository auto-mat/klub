from aklub.filters import unit_admin_mixin_generator

from django.contrib import admin

from import_export_celery.admin import ExportJobAdmin, ImportJobAdmin
from import_export_celery.models import ExportJob, ImportJob

import nested_admin

from related_admin import RelatedFieldAdmin

from .models import ExportConnector, ImportConnector


class InlineMixin(object):
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            if db_field.name == 'administrative_unit':
                kwargs["queryset"] = request.user.administrated_units.all()
                kwargs["required"] = True
                kwargs["initial"] = kwargs["queryset"].first()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ImportAdminInline(InlineMixin, nested_admin.NestedStackedInline):
    model = ImportConnector


admin.site.unregister(ImportJob)


@admin.register(ImportJob)
class _ImportJobAdmin(
    unit_admin_mixin_generator('importconnector__administrative_unit'),
    ImportJobAdmin,
    RelatedFieldAdmin,
):
    inlines = (ImportAdminInline,)

    list_display = ImportJobAdmin.list_display + (
        'importconnector__administrative_unit',
    )


class ExportAdminInline(InlineMixin, nested_admin.NestedStackedInline):
    model = ExportConnector


admin.site.unregister(ExportJob)


@admin.register(ExportJob)
class _ExportJobAdmin(
    unit_admin_mixin_generator('exportconnector__administrative_unit'),
    ExportJobAdmin,
    RelatedFieldAdmin,
):
    inlines = (ExportAdminInline,)

    list_display = ExportJobAdmin.list_display + (
        'exportconnector__administrative_unit',
    )
