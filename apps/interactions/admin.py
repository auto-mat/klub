from aklub.models import Event

from django.contrib import admin
from django.core import serializers

from related_admin import RelatedFieldAdmin

from .forms import InteractionInlineForm, InteractionInlineFormset
from .models import Interaction, InteractionCategory, InteractionType, Result


@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Interaction)
class InteractionAdmin(RelatedFieldAdmin, admin.ModelAdmin):
    list_display = (
                'user',
                'type__name',
                'date_from',
                'subject',
                'administrative_unit',
            )
    ordering = ('-date_from',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.has_perm('aklub.can_edit_all_units'):
                fields = []
            else:
                if request.user.administrated_units.all().first() == obj.administrative_unit:
                    fields = []
                else:
                    fields = [f.name for f in self.model._meta.fields]
        else:
            fields = []
        return fields

    def change_view(self, request, object_id, form_url='', extra_context=None):
        data = {}
        data['display_fields'] = serializers.serialize('json', InteractionType.objects.all())
        data['required_fields'] = [field.name for field in Interaction._meta.get_fields() if not field.null]
        return super().change_view(request, object_id, form_url, extra_context=data,)

    def add_view(self, request, form_url='', extra_context=None):
        data = {}
        data['display_fields'] = serializers.serialize('json', InteractionType.objects.all())
        data['required_fields'] = [field.name for field in Interaction._meta.get_fields() if not field.null]
        return super().add_view(request, form_url, extra_context=data,)


@admin.register(InteractionCategory)
class InteractionCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sort',
    )
    save_as = True


class InteractionInline(admin.StackedInline):
    model = Interaction
    formset = InteractionInlineFormset
    form = InteractionInlineForm
    can_delete = True
    extra = 0
    readonly_fields = ('created_by', 'handled_by', 'created', 'updated')
    fk_name = 'user'

    fieldsets = (
        (None, {
            'fields': (
                ('type', 'administrative_unit', 'subject', 'event', 'date_from', 'date_to',
                 'settlement', 'note', 'text', 'attachment', 'summary', 'status',
                 'result', 'rating', 'next_step', 'next_communication_date', 'created_by', 'handled_by',
                 'created', 'updated', 'communication_type', 'dispatched'),
            ),
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Event.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Event.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
