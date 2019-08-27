
'''
This file changes (monkey-patching) third-party applications for the purpose of this application.
'''
from django.db import models

from smmapdfs.admin import PdfSandwichAdmin as PdfSandwichFontAdmin, PdfSandwichEmailAdmin,   PdfSandwichTypeAdmin
from smmapdfs.models import PdfSandwichEmail, PdfSandwichFont, PdfSandwichType


def monkey_admin_smmapdfs():
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            if db_field.name == 'administrative_unit':
                kwargs['queryset'] = request.user.administrated_units.all()
                kwargs['required'] = True
                kwargs['initial'] = request.user.administrated_units.all()
            if db_field.name == 'pdfsandwich_type':
                kwargs['queryset'] = PdfSandwichType.objects.filter(administrative_unit=request.user.administrative_units.first())
        return super(self.__class__, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        queryset = super(self.__class__, self).get_queryset(request)
        if request.user.has_perm('aklub.can_edit_all_units'):
            return queryset
        kwargs = {self.queryset_unit_param + '__in': request.user.administrated_units.all()}
        return queryset.filter(**kwargs).distinct()  # The distinct is necessarry here for unit admins, that have more cities

    PdfSandwichTypeAdmin.queryset_unit_param = 'administrative_unit'
    PdfSandwichTypeAdmin.get_queryset = get_queryset
    PdfSandwichTypeAdmin.formfield_for_foreignkey = formfield_for_foreignkey

    PdfSandwichEmailAdmin.queryset_unit_param = 'administrative_unit'
    PdfSandwichEmailAdmin.get_queryset = get_queryset
    PdfSandwichEmailAdmin.formfield_for_foreignkey = formfield_for_foreignkey

    PdfSandwichFontAdmin.queryset_unit_param = 'administrative_unit'
    PdfSandwichFontAdmin.get_queryset = get_queryset
    PdfSandwichFontAdmin.formfield_for_foreignkey = formfield_for_foreignkey


def monkey_model_smmapdfs():
    models.ForeignKey(
                    'aklub.AdministrativeUnit',
                    null=True,
                    blank=True,
                    on_delete=models.CASCADE,).contribute_to_class(PdfSandwichType, 'administrative_unit')
    models.ForeignKey(
                    'aklub.AdministrativeUnit',
                    null=True,
                    blank=True,
                    on_delete=models.CASCADE,).contribute_to_class(PdfSandwichFont, 'administrative_unit')
    models.ForeignKey(
                    'aklub.AdministrativeUnit',
                    null=True,
                    blank=True,
                    on_delete=models.CASCADE,).contribute_to_class(PdfSandwichEmail, 'administrative_unit')
