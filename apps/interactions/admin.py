from aklub.models import AdministrativeUnit, CompanyContact, Profile, ProfileEmail

from django.contrib import admin
from django.core import serializers
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from events.models import Event

from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from import_export_celery.admin_actions import create_export_job_action

from related_admin import RelatedFieldAdmin

from .forms import InteractionInlineForm, InteractionInlineFormset
from .models import (
    Interaction,
    InteractionCategory,
    InteractionStatus,
    InteractionType,
    PetitionSignature,
    Result,
)
from . import tasks
from . import filters

from events.filters import MultiSelectFilter


@admin.register(InteractionType)
class InteractionTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "id", "slug", "send_email", "send_sms"]


class InteractionWidget(ForeignKeyWidget):
    """Handle ForeignKey no exist error"""

    def get_queryset(self, value, row):
        values = self.model.objects.filter(id=value)
        if values:
            return values
        else:
            raise ValueError(" This id doesn't exist")


class InteractionResource(ModelResource):
    profile_type = fields.Field()
    email = fields.Field()
    type = fields.Field(
        attribute="type", widget=InteractionWidget(InteractionType)
    )  # noqa
    event = fields.Field(attribute="event", widget=InteractionWidget(Event))
    created_by = fields.Field(attribute="created_by", widget=InteractionWidget(Profile))
    handled_by = fields.Field(attribute="handled_by", widget=InteractionWidget(Profile))
    result = fields.Field(attribute="result", widget=InteractionWidget(Result))
    administrative_unit = fields.Field(
        attribute="administrative_unit", widget=InteractionWidget(AdministrativeUnit)
    )

    class Meta:
        model = Interaction

        fields = (
            "email",
            "user",
            "type",
            "administrative_unit",
            "subject",
            "date_from",  # required fields
            "dispatched",  # It shoud be true or email are send (if type.send_email == True).
            "event",
            "date_to",
            "next_communication_date",
            "settlement",
            "note",
            "summary",
            "status",
            "result",
            "rating",
            "next_step",
            "communication_type",
            "created_by",
            "handled_by",
            "created",
            "updated",  # readonly fields
        )
        clean_model_instances = True
        import_id_fields = (
            []
        )  # must be empty or library take field id as default and ignore before_import_row

    def before_import_row(self, row, **kwargs):  # noqa
        user = None
        if row.get("profile_type") not in ["u", "c"]:
            raise ValidationError(
                {"profile_type": _('Insert "c" or "u" (company/user)')}
            )
        if not row.get("email") and not row.get("user"):
            raise ValidationError({"email": _("Email or Username must be set")})
        if row.get("email"):
            row["email"] = row["email"].lower()
            try:
                if row.get("profile_type") == "u":
                    user = ProfileEmail.objects.get(email=row["email"]).user
                else:
                    user = CompanyContact.objects.get(email=row["email"]).company
            except (ProfileEmail.DoesNotExist, CompanyContact.DoesNotExist):
                pass
        if row.get("user") and not user:
            try:
                user = Profile.objects.get(username=row["user"])
            except Profile.DoesNotExist:
                pass
        if user:
            row["user"] = user.id
            return row
        else:
            raise ValidationError(
                {"user": _("User with this username or email doesnt exist")}
            )

    def dehydrate_user(self, interaction):
        if hasattr(interaction, "user"):
            return interaction.user

    def dehydrate_email(self, interaction):
        if hasattr(interaction, "user"):
            return interaction.user.get_email_str()

    def dehydrate_profile_type(self, interaction):
        if hasattr(interaction, "user"):
            value = "c"
            if interaction.user.is_userprofile():
                value = "u"
            return value


def sync_with_daktela(self, request, queryset):
    tasks.sync_with_daktela.delay(list(queryset.values_list("pk", flat=True)))


sync_with_daktela.short_description = _("Sync interactions with Daktela app tickets")


@admin.register(Interaction)
class InteractionAdmin(ImportExportMixin, RelatedFieldAdmin, admin.ModelAdmin):
    resource_class = InteractionResource
    autocomplete_fields = ("user",)
    import_template_name = "admin/import_export/userprofile_import.html"

    list_display = (
        "user",
        "type__name",
        "date_from",
        "subject",
        "administrative_unit",
        "created_by",
        "handled_by",
        "created",
        "updated",
        "rating",
        "status",
    )
    ordering = ("-date_from",)

    readonly_fields = (
        "updated",
        "created",
        "created_by",
        "handled_by",
    )

    search_fields = [
        "id",
        "user__username",
        "user__userprofile__first_name",
        "user__userprofile__last_name",
        "user__companyprofile__name",
        "user__userprofile__profileemail__email",
        "skills",
    ]

    # autocomplete_fields = ('user', 'event',)
    list_filter = (
        "type__name",
        "date_from",
        "administrative_unit",
        ("program_of_interest", MultiSelectFilter),
        filters.EventInteractionNameFilter,
        filters.EventInteractionId,
    )

    actions = (create_export_job_action, sync_with_daktela)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["type"].queryset = form.base_fields["type"].queryset.order_by(
            "name"
        )
        if request.user.is_staff:
            form.base_fields[
                "administrative_unit"
            ].initial = request.user.administrative_units.first()
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm("aklub.can_edit_all_units"):
                kwargs["queryset"] = Event.objects.filter(
                    administrative_units__in=request.user.administrated_units.all()
                )
            else:
                kwargs["queryset"] = Event.objects.all()
        if db_field.name == "administrative_unit":
            if not request.user.has_perm("aklub.can_edit_all_units"):
                kwargs["queryset"] = request.user.administrated_units.all()
            else:
                kwargs["queryset"] = AdministrativeUnit.objects.all()
        if db_field.name == "user":
            if not request.user.has_perm("aklub.can_edit_all_units"):
                kwargs["queryset"] = Profile.objects.filter(
                    administrative_units__in=request.user.administrated_units.all()
                )
            else:
                kwargs["queryset"] = Profile.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.has_perm("aklub.can_edit_all_units"):
                fields = super().get_readonly_fields(request, obj)
            else:
                if (
                    request.user.administrated_units.all().first()
                    == obj.administrative_unit
                ):
                    fields = super().get_readonly_fields(request, obj)
                else:
                    fields = [f.name for f in self.model._meta.fields]
        else:
            fields = []
        return fields

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "administrative_unit",
                "type",
                "user__userprofile",
                "user__companyprofile",
            )
        )
        if not request.user.has_perm("aklub.can_edit_all_units"):
            qs = qs.filter(
                user__administrative_units=request.user.administrated_units.first()
            )
        return qs

    def change_view(self, request, object_id, form_url="", extra_context=None):
        data = {}
        data["display_fields"] = serializers.serialize(
            "json", InteractionType.objects.all()
        )
        data["required_fields"] = [
            field.name for field in Interaction._meta.get_fields() if not field.blank
        ]
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=data,
        )

    def add_view(self, request, form_url="", extra_context=None):
        data = {}
        data["display_fields"] = serializers.serialize(
            "json", InteractionType.objects.all()
        )
        data["required_fields"] = [
            field.name for field in Interaction._meta.get_fields() if not field.blank
        ]
        return super().add_view(
            request,
            form_url,
            extra_context=data,
        )

    def get_changeform_initial_data(self, request, *args, **kwargs):
        """
        if filter on current user is active -> fill user field in add form
        (can happen if view older interactions is clicked in profile)
        """
        initial = super().get_changeform_initial_data(request)
        if initial and "user" in initial.get("_changelist_filters"):
            get_data = initial["_changelist_filters"].split("&")
            user = [user for user in get_data if "user" in user][0].split("=")[1]
            return {
                "user": user,
            }

    def delete_queryset(self, request, queryset):
        tasks.delete_tickets_from_daktela.delay(
            list(queryset.values_list("pk", flat=True)),
        )


@admin.register(InteractionCategory)
class InteractionCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(InteractionStatus)
class InteractionStatusAdmin(admin.ModelAdmin):
    pass


@admin.register(PetitionSignature)
class PetitionSignatureAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "created", "email_confirmed", "gdpr_consent")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sort",
    )
    save_as = True


class InteractionInline(admin.StackedInline):
    model = Interaction
    formset = InteractionInlineFormset
    form = InteractionInlineForm
    can_delete = True
    extra = 0
    # autocomplete_fields = ('event',)
    readonly_fields = ("created_by", "handled_by", "created", "updated")
    fk_name = "user"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("type", "administrative_unit", "subject"),
                    ("date_from", "date_to", "next_communication_date"),
                    ("status", "dispatched"),
                    (
                        "event",
                        "summary",
                    ),
                ),
            },
        ),
        (
            ("Details"),
            {
                "classes": ("collapse",),
                "fields": (
                    "note",
                    "attachment",
                    "communication_type",
                    ("result", "rating"),
                    "next_step",
                    "settlement",
                    ("created_by", "created"),
                    ("handled_by", "updated"),
                ),
            },
        ),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm("aklub.can_edit_all_units"):
                kwargs["queryset"] = Event.objects.filter(
                    administrative_units__in=request.user.administrated_units.all()
                )
            else:
                kwargs["queryset"] = Event.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
