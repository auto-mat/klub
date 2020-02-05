from aklub.models import Event

from django.contrib import admin
from django.core import serializers

from .models import Interaction, InteractionCategory, InteractionType, Result


@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
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
    can_delete = True
    extra = 0
    readonly_fields = ('created_by', 'handled_by', 'created', 'updated')
    fk_name = 'user'

    fieldsets = (
        (None, {
            'fields': (
                ('type', 'administrative_unit', 'event',
                 'settlement', 'note', 'text', 'attachment', 'subject', 'summary', 'status',
                 'result', 'rating', 'next_step', 'next_communication_date', 'created_by', 'handled_by',
                 'date_from', 'date_to', 'created', 'updated', 'send', 'communication_type', 'dispatched'),
            ),
        }),
    )
    """
    def get_queryset(self, request):
        qs = super(InteractionInline, self).get_queryset(request)
        qs = qs.filter(type__in=('individual', 'auto')).order_by('-date')
        qs = qs.select_related('created_by', 'handled_by')
        return qs
    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Event.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Event.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
