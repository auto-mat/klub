
from aklub.filters import unit_admin_mixin_generator
from aklub.models import TaxConfirmationField

from django.contrib import admin
from django.forms.models import ModelForm

from related_admin import RelatedFieldAdmin

from smmapdfs.admin import PdfSandwichEmailAdmin, PdfSandwichTypeAdmin
from smmapdfs.models import PdfSandwichEmail, PdfSandwichType

from .models import PdfSandwichEmailConnector, PdfSandwichTypeConnector


class PdfInlineMixinForm(ModelForm):
    def has_changed(self):
        """ Must return True if we want to save unchanged inlines
            or raise validation errors """
        return True


class PdfInlineMixin(object):
    can_delete = False
    form = PdfInlineMixinForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'administrative_unit':
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = request.user.administrated_units.all()
                kwargs["initial"] = kwargs["queryset"].first()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PdfEmailAdminInline(PdfInlineMixin, admin.StackedInline):
    model = PdfSandwichEmailConnector


class PdfTypeAdminInline(PdfInlineMixin, admin.StackedInline):
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


class PdfFieldsInline(admin.TabularInline):
    model = TaxConfirmationField
    can_delete = True
    extra = 0

    def formfield_for_choice_field(self, db_field, request, *args, **kwargs):
        if db_field.name == "field":
            try:  # what if connector doesnt exist?
                if self.obj.pdfsandwichtypeconnector.profile_type == 'company_profile':
                    kwargs['choices'] = [(a, a) for a in TaxConfirmationField.fields_company.keys()]
                else:
                    kwargs['choices'] = [(a, a) for a in TaxConfirmationField.fields_user.keys()]
            except PdfSandwichTypeConnector.DoesNotExist:
                pass
        return super().formfield_for_choice_field(db_field, request, *args, **kwargs)


admin.site.unregister(PdfSandwichType)
@admin.register(PdfSandwichType)
class _PdfSandwichTypeAdmin(
    unit_admin_mixin_generator('pdfsandwichtypeconnector__administrative_unit'),
    RelatedFieldAdmin, PdfSandwichTypeAdmin,
):
    inlines = (PdfTypeAdminInline, PdfFieldsInline)

    list_display = PdfSandwichTypeAdmin.list_display + (
        'pdfsandwichtypeconnector__administrative_unit',
        'pdfsandwichtypeconnector__profile_type'
    )

    def get_inline_instances(self, request, obj=None):
        if obj:
            inlines = [inline(self.model, self.admin_site) for inline in self.inlines]
        else:
            inlines = [inline(self.model, self.admin_site) for inline in self.inlines if inline.__name__ not in ['PdfFieldsInline', ]]
        for i in range(len(inlines)):
            inlines[i].obj = obj
        return inlines
