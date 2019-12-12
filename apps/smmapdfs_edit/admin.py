
from aklub.filters import unit_admin_mixin_generator
from aklub.models import TaxConfirmationField, TaxConfirmationPdf

from django.contrib import admin

import nested_admin

from related_admin import RelatedFieldAdmin

from smmapdfs.admin import PdfSandwichEmailAdmin, PdfSandwichTypeAdmin
from smmapdfs.admin_abcs import PdfSandwichAdmin, PdfSandwichFieldAdmin
from smmapdfs.models import PdfSandwichEmail, PdfSandwichFont, PdfSandwichType

from .models import PdfSandwichEmailConnector, PdfSandwichTypeConnector


class PdfInlineMixin(object):
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            if db_field.name == 'administrative_unit':
                kwargs["queryset"] = request.user.administrated_units.all()
                kwargs["required"] = True
                kwargs["initial"] = kwargs["queryset"].first()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PdfEmailAdminInline(PdfInlineMixin, nested_admin.NestedStackedInline):
    model = PdfSandwichEmailConnector


class PdfTypeAdminInline(PdfInlineMixin, nested_admin.NestedStackedInline):
    model = PdfSandwichTypeConnector


admin.site.unregister(PdfSandwichEmail)
@admin.register(PdfSandwichEmail)
class _PdfSandwichEmailAdmin(
    unit_admin_mixin_generator('pdfsandwichemailconnector__administrative_unit'),
    RelatedFieldAdmin, PdfSandwichTypeAdmin,
):

    inlines = (PdfEmailAdminInline,)

    list_display = PdfSandwichEmailAdmin.list_display + (
        'pdfsandwichemailconnector__administrative_unit',
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pdfsandwich_type":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = PdfSandwichType.objects.filter(
                    pdfsandwichtypeconnector__administrative_unit__in=request.user.administrated_units.all(),
                )
            else:
                return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.unregister(PdfSandwichType)
@admin.register(PdfSandwichType)
class _PdfSandwichTypeAdmin(
    unit_admin_mixin_generator('pdfsandwichtypeconnector__administrative_unit'),
    RelatedFieldAdmin, PdfSandwichTypeAdmin,
):
    inlines = (PdfTypeAdminInline,)

    list_display = PdfSandwichTypeAdmin.list_display + (
        'pdfsandwichtypeconnector__administrative_unit',
    )


class TaxConfirmationPdfAdmin(
    unit_admin_mixin_generator('pdfsandwich_type__pdfsandwichtypeconnector__administrative_unit'),
    PdfSandwichAdmin,
):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            if db_field.name == 'pdfsandwich_type':
                kwargs["queryset"] = PdfSandwichType.objects.filter(
                                        pdfsandwichtypeconnector__administrative_unit__in=request.user.administrated_units.all(),
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TaxConfirmationFieldAdmin(
    unit_admin_mixin_generator('pdfsandwich_type__pdfsandwichtypeconnector__administrative_unit'),
    PdfSandwichFieldAdmin,
):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            if db_field.name == 'pdfsandwich_type':
                kwargs["queryset"] = PdfSandwichType.objects.filter(
                                        pdfsandwichtypeconnector__administrative_unit__in=request.user.administrated_units.all(),
                )
            if db_field.name == 'font':
                kwargs["queryset"] = PdfSandwichFont.objects.filter(
                                        pdfsandwichfontconnector__administrative_unit__in=request.user.administrated_units.all(),
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(TaxConfirmationPdf, TaxConfirmationPdfAdmin)
admin.site.register(TaxConfirmationField, TaxConfirmationFieldAdmin)
