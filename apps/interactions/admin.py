from aklub.models import AdministrativeUnit, Event, Profile, ProfileEmail

from django.contrib import admin
from django.core import serializers
from django.core.exceptions import ValidationError

from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from related_admin import RelatedFieldAdmin

from .forms import InteractionInlineForm, InteractionInlineFormset
from .models import Interaction, InteractionCategory, InteractionType, Result


@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    pass


class InteractionWidget(ForeignKeyWidget):
    """ Handle ForeignKey no exist error """
    def get_queryset(self, value, row):
        values = self.model.objects.filter(id=value)
        if values:
            return values
        else:
            raise ValueError(" This id doesn't exist")


class InteractionResource(ModelResource):
    email = fields.Field()
    type = fields.Field(attribute='type', widget=InteractionWidget(InteractionType)) # noqa
    event = fields.Field(attribute='event', widget=InteractionWidget(Event))
    created_by = fields.Field(attribute='created_by', widget=InteractionWidget(Profile))
    handled_by = fields.Field(attribute='handled_by', widget=InteractionWidget(Profile))
    result = fields.Field(attribute='result', widget=InteractionWidget(Result))
    administrative_unit = fields.Field(attribute='administrative_unit', widget=InteractionWidget(AdministrativeUnit))

    class Meta:
        model = Interaction

        fields = (
            'email', 'user', 'type', 'administrative_unit', 'subject', 'date_from',  # required fields
            'dispatched',  # It shoud be true or email are send (if type.send_email == True).
            'event',  'date_to', 'next_communication_date',
            'settlement', 'note', 'summary', 'status', 'result', 'rating',
            'next_step', 'communication_type',
            'created_by', 'handled_by', 'created', 'updated',  # readonly fields




         )
        clean_model_instances = True

    def before_import_row(self, row, **kwargs):
        user = None
        if row.get('email'):
            try:
                user = ProfileEmail.objects.get(email=row['email']).user
            except ProfileEmail.DoesNotExist:
                pass
        if row.get('user') and not user:
            try:
                user = Profile.objects.get(username=row['user'])
            except Profile.DoesNotExist:
                pass
        if user:
            row['user'] = user.id
            return row
        else:
            raise ValidationError({'user': 'User with this username or email doesnt exist'})

    def dehydrate_user(self, interaction):
        if hasattr(interaction, 'user'):
            return interaction.user

    def dehydrate_email(self, interaction):
        if hasattr(interaction, 'user'):
            return interaction.user.get_email_str()


@admin.register(Interaction)
class InteractionAdmin(ImportExportMixin, RelatedFieldAdmin, admin.ModelAdmin):

    resource_class = InteractionResource

    list_display = (
                'user',
                'type__name',
                'date_from',
                'subject',
                'administrative_unit',
                'created_by',
                'handled_by',
                'created',
                'updated',
            )
    ordering = ('-date_from',)

    readonly_fields = ("updated", "created", "created_by", "handled_by", )

    search_fields = ['user__username', ]

    autocomplete_fields = ('user', 'event',)
    list_filter = (
                'type__name',
                'date_from',
                'administrative_unit',
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Event.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Event.objects.all()
        if db_field.name == "administrative_unit":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = request.user.administrated_units.all()
            else:
                kwargs["queryset"] = AdministrativeUnit.objects.all()
        if db_field.name == "user":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Profile.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Profile.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.has_perm('aklub.can_edit_all_units'):
                fields = super().get_readonly_fields(request, obj)
            else:
                if request.user.administrated_units.all().first() == obj.administrative_unit:
                    fields = super().get_readonly_fields(request, obj)
                else:
                    fields = [f.name for f in self.model._meta.fields]
        else:
            fields = []
        return fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.has_perm('aklub.can_edit_all_units'):
            qs = qs.filter(user__administrative_units=request.user.administrated_units.first())
        return qs

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
    autocomplete_fields = ('event',)
    readonly_fields = ('created_by', 'handled_by', 'created', 'updated')
    fk_name = 'user'

    fieldsets = (
        (None, {
            'fields': (
                ('type', 'administrative_unit', 'subject'),
                ('date_from', 'date_to', 'next_communication_date'),
                ('status', 'dispatched'),
                ('event', 'summary', ),
            ),
        }),
        (('Details'), {
            'classes': ('collapse',),
            'fields': (
             'note', 'attachment', 'communication_type',
             ('result', 'rating'),
             'next_step',
             'settlement',
             ('created_by', 'created'),
             ('handled_by', 'updated'),
            ),
        }
         )
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Event.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Event.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
