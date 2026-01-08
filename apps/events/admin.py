import datetime
import json

from aklub import darujme
from aklub.filters import unit_admin_mixin_generator

from api.serializers import EventSerializer

from django.contrib import admin
from django.db.models import Case, CharField, Q, Sum, Value, When, F
from django.db.models.functions import Concat
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

from import_export.admin import ImportExportMixin
from import_export_celery.admin_actions import create_export_job_action
from import_export.resources import ModelResource
from rangefilter.filter import DateTimeRangeFilter
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

from . import filters
from .admin_views import EventChangeList
from .forms import EventForm, EventChangeListForm
from events.models import (
    Agreement,
    Category,
    Event,
    EventType,
    Invoice,
    Location,
    OrganizationPosition,
    OrganizationTeam,
    Qualification,
)


def download_darujme_statement(self, request, queryset):
    payments = []
    skipped_payments = []
    for campaign in queryset.all():
        payment, skipped = darujme.create_statement_from_API(campaign)
        payments.append(payment)
        skipped_payments += skipped

    self.message_user(
        request,
        format_html(
            "Created following account statements: {}<br/>Skipped payments: {}",
            ", ".join([str(p.id) if p else "" for p in payments]),
            skipped_payments,
        ),
    )


download_darujme_statement.short_description = _("Download darujme statements")


# @admin.register(OrganizationPosition)
class OrganizationPositionAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "specific_name",
        "place",
        "region",
        "gps_latitude",
        "gps_longitude",
    )


# @admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


# @admin.register(Qualification)
class Qualificationdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviated_name")


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ("id", "get_event_name", "get_user_name", "status", "created", "updated")
    list_filter = ("status", "created", "updated")
    search_fields = ("event__name", "note", "event__organization_team__profile__first_name", "event__organization_team__profile__last_name")
    readonly_fields = ("created", "updated")
    fields = ("event", "status", "pdf_file", "pdf_file_signed", "pdf_file_completed", "note", "created", "updated")
    
    def get_event_name(self, obj):
        """Return the event name"""
        return obj.event.name if obj.event else "-"
    
    get_event_name.short_description = _("Event Name")
    get_event_name.admin_order_field = "event__name"
    
    def get_user_name(self, obj):
        """Return the organizer/user name(s)"""
        if not obj.event:
            return "-"
        
        names = []
        for profile in obj.event.organization_team.all():
            if profile.is_userprofile():
                # UserProfile
                name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
                if name:
                    names.append(name)
            elif hasattr(profile, 'name') and profile.name:
                # CompanyProfile or other profile type
                names.append(profile.name)
        
        return ", ".join(names) if names else "-"
    
    get_user_name.short_description = _("Organizer")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "get_event_name", "get_user_name", "status", "created", "updated")
    list_filter = ("status", "created", "updated")
    search_fields = ("event__name", "invoice_number", "event__organization_team__profile__first_name", "event__organization_team__profile__last_name")
    readonly_fields = ("created", "updated")
    fields = ("event", "status", "pdf_file", "invoice_number", "amount", "due_date", "note", "created", "updated")
    
    def get_event_name(self, obj):
        """Return the event name"""
        return obj.event.name if obj.event else "-"
    
    get_event_name.short_description = _("Event Name")
    get_event_name.admin_order_field = "event__name"
    
    def get_user_name(self, obj):
        """Return the organizer/user name(s)"""
        if not obj.event:
            return "-"
        
        names = []
        for profile in obj.event.organization_team.all():
            if profile.is_userprofile():
                # UserProfile
                name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
                if name:
                    names.append(name)
            elif hasattr(profile, 'name') and profile.name:
                # CompanyProfile or other profile type
                names.append(profile.name)
        
        return ", ".join(names) if names else "-"
    
    get_user_name.short_description = _("Organizer")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "id")
    search_fields = ("name", "slug", "description")
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class OrganizationTeamInline(admin.TabularInline):
    model = OrganizationTeam
    autocomplete_fields = ["profile"]
    classes = ["collapse"]
    extra = 0


class EventResource(ModelResource):
    class Meta:
        model = Event


@admin.register(Event)
class EventAdmin(
    unit_admin_mixin_generator("administrative_units"),
    ImportExportMixin,
    TreeNodeModelAdmin,
):
    main_coordinator_name = _("Hlavní organizátor")
    secondary_coordinator_name = _("Vedlejší oraganizátor")
    none_val = "-"
    yes_icon = '<img src="/media/admin/img/icon-yes.svg" alt="True"/>'
    no_icon = '<img src="/media/admin/img/icon-no.svg" alt="False"/>'
    form = EventForm
    inlines = (OrganizationTeamInline,)
    list_display = (
        "name",
        "slug",
        "specific_location_name",
        "datetime_from",
        "local_organizer",
        "main_coordinator",
        "main_coordinator_email",
        "main_coordinator_telephone",
        "note",
        "go_to_users",
        # TODO: must be optimalized
        # 'number_of_recruiters',
        # 'yield_total',
        # 'total_expenses',
        # 'expected_monthly_income',
        # 'return_of_investmensts',
        # 'average_yield',
        # 'average_expense',
    )
    list_editable = ("note",)
    list_filter = [
        ("donorpaymentchannel__payment__date", filters.EventYieldDateRangeFilter),
        "grant",
        ("diet", filters.MultiSelectFilter),
        ("datetime_from", DateTimeRangeFilter),
        ("datetime_to", DateTimeRangeFilter),
        filters.EventParentFilter,
        filters.EventChildrenFilter,
        filters.EventAncestorsFilter,
        filters.EventDescendantsFilter,
        filters.EventInteractionFilter,
        filters.EventInteractionWithStatusFilter,
        filters.EventUserInteractionFilter,
        filters.EventLocationRegionFilter,
    ]
    readonly_fields = (
        "get_program_items",
        "get_organizers",
        "get_company",
        "number_of_members",
        "number_of_recruiters",
        "yield_total",
        "total_expenses",
        "expected_monthly_income",
        "return_of_investmensts",
        "average_yield",
        "average_expense",
        "go_to_users",
    )
    search_fields = ("name",)
    actions = (download_darujme_statement, create_export_job_action)
    save_as = True

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "basic_purpose",
                    "opportunity",
                    "grant",
                    ("datetime_from"),
                    "variable_symbol_prefix",
                    "location"
                ),
            },
        ),
        (
            _("Detail information"),
            {
                "classes": ("collapse",),
                "fields": (
                    "main_photo",
                    "description",
                    "url_title",
                    "url",
                    "url_title1",
                    "url1",
                    "url_title2",
                    "url2",
                ),
            },
        ),
        (
            _("Web setting"),
            {
                "classes": ("collapse",),
                "fields": (
                    "enable_signing_petitions",
                    "enable_registration",
                    "allow_statistics",
                    "public_on_web",
                    "public_on_web_date_from",
                    "public_on_web_date_to",
                    "email_confirmation_redirect",
                    "entry_form_url",
                    "web_url",
                ),
            },
        ),
        (
            _("Program"),
            {
                "classes": ("collapse",),
                "fields": (
                    "get_program_items",
                    "get_organizers",
                    "get_company",
                ),
            },
        ),
    )
    resource_class = EventResource

    def get_queryset(self, request):
        donor_filter = {}
        extra_filters = request.GET
        dpd_gte = extra_filters.get("donorpaymentchannel__payment__date__range__gte")
        dpd_lte = extra_filters.get("donorpaymentchannel__payment__date__range__lte")
        if dpd_gte:
            donor_filter[
                "donorpaymentchannel__payment__date__gte"
            ] = datetime.datetime.strptime(dpd_gte, "%d.%m.%Y")
        if dpd_lte:
            donor_filter[
                "donorpaymentchannel__payment__date__lte"
            ] = datetime.datetime.strptime(dpd_lte, "%d.%m.%Y")
        queryset = (
            super()
            .get_queryset(request)
            .annotate(
                sum_yield_amount=Sum(
                    "donorpaymentchannel__payment__amount", filter=Q(**donor_filter)
                ),
            )
        )
        return queryset

    def _extra_view_context(self):
        return {
            "serialized_fields": EventSerializer.Meta.fields,
            "hide_list": json.dumps(
                {
                    "action": [
                        "opportunity",
                        "grant",
                        "variable_symbol_prefix",
                        "total_working_days",
                        "working_hours",
                        "enable_signing_petitions",
                        "enable_registration",
                        "allow_statistics",
                        "email_confirmation_redirect",
                        "number_of_recruiters",
                        "yield_total",
                        "real_yield",
                        "expected_monthly_income",
                        "return_of_investmensts",
                        "average_yield",
                        "average_expense",
                    ],
                    "action-with-attendee-list": [
                        "opportunity",
                        "grant",
                        "variable_symbol_prefix",
                        "total_working_days",
                        "working_hours",
                        "enable_signing_petitions",
                        "enable_registration",
                        "allow_statistics",
                        "email_confirmation_redirect",
                        "number_of_recruiters",
                        "yield_total",
                        "real_yield",
                        "expected_monthly_income",
                        "return_of_investmensts",
                        "average_yield",
                        "average_expense",
                    ],
                    "petition": [],
                    "camp": [
                        "opportunity",
                        "grant",
                        "variable_symbol_prefix",
                        "enable_signing_petitions",
                        "enable_registration",
                        "allow_statistics",
                        "email_confirmation_redirect",
                        "number_of_recruiters",
                        "yield_total",
                        "real_yield",
                        "total_expenses",
                        "expected_monthly_income",
                        "return_of_investmensts",
                        "average_yield",
                        "average_expense",
                    ],
                    "opportunity": [
                        "grant",
                        "variable_symbol_prefix",
                        "description",
                        "age_from",
                        "age_to",
                        "event_type",
                        "program",
                        "intended_for",
                        "location",
                        "registration_method",
                        "participation_fee",
                        "meeting",
                        "focus_on_members",
                        "note",
                        "number_of_actions",
                        "promoted_in_magazine",
                        "total_working_days",
                        "working_hours",
                        "accommodation",
                        "diet",
                        "comment_on_work_done",
                        "other_work",
                        "enable_signing_petitions",
                        "enable_registration",
                        "allow_statistics",
                        "public_on_web",
                        "email_confirmation_redirect",
                        "entry_form_url",
                        "web_url",
                        "additional_question_1",
                        "additional_question_2",
                        "additional_question_3",
                        "additional_question_4",
                        "additional_photo_1",
                        "additional_photo_2",
                        "additional_photo_3",
                        "additional_photo_4",
                        "additional_photo_5",
                        "additional_photo_6",
                        "number_of_members",
                        "number_of_recruiters",
                        "yield_total",
                        "real_yield",
                        "total_expenses",
                        "expected_monthly_income",
                        "return_of_investmensts",
                        "average_yield",
                        "average_expense",
                        "hours_worked",
                        "total_participants",
                        "total_participants_under_26",
                    ],
                    "campaign": [
                        "opportunity",
                        "grant",
                        "variable_symbol_prefix",
                        "age_from",
                        "age_to",
                        "event_type",
                        "program",
                        "intended_for",
                        "location",
                        "registration_method",
                        "participation_fee",
                        "meeting",
                        "focus_on_members",
                        "note",
                        "number_of_actions",
                        "promoted_in_magazine",
                        "total_working_days",
                        "working_hours",
                        "accommodation",
                        "diet",
                        "contact_person_name",
                        "contact_person_email",
                        "contact_person_telephone",
                        "comment_on_work_done",
                        "other_work",
                        "enable_signing_petitions",
                        "allow_statistics",
                        "public_on_web",
                        "public_on_web_date_from",
                        "public_on_web_date_to",
                        "email_confirmation_redirect",
                        "entry_form_url",
                        "additional_question_1",
                        "additional_question_2",
                        "additional_question_3",
                        "additional_question_4",
                        "main_photo",
                        "additional_photo_1",
                        "additional_photo_2",
                        "additional_photo_3",
                        "additional_photo_4",
                        "additional_photo_5",
                        "additional_photo_6",
                        "invitation_text_short",
                        "invitation_text_1",
                        "invitation_text_2",
                        "invitation_text_3",
                        "invitation_text_4",
                        "url_title",
                        "url",
                        "url_title1",
                        "url1",
                        "url_title2",
                        "url2",
                        "print_point_1",
                        "print_point_2",
                        "print_point_3",
                        "print_point_4",
                        "print_point_5",
                        "print_point_6",
                        "event",
                        "number_of_members",
                        "number_of_recruiters",
                        "yield_total",
                        "real_yield",
                        "total_expenses",
                        "expected_monthly_income",
                        "return_of_investmensts",
                        "average_yield",
                        "average_expense",
                        "hours_worked",
                        "total_participants",
                        "total_participants_under_26",
                    ],
                    "zmj_location": [
                        "registration_method",
                        "additional_question_1",
                        "additional_question_2",
                        "additional_question_3",
                        "additional_question_4",
                        "invitation_text_short",
                        "invitation_text_1",
                        "invitation_text_2",
                        "invitation_text_3",
                        "invitation_text_4",
                        "number_of_actions",
                        "opportunity",
                        "is_internal",
                        "age_from",
                        "age_to",
                        "intended_for",
                        "participation_fee",
                        "responsible_person",
                        "meeting",
                        "grant",
                        "focus_on_members",
                        "vip_action",
                        "promoted_in_magazine",
                        "hours_worked",
                        "variable_symbol_prefix",
                        "description",
                        "real_yield",
                        "datetime_from",
                        "start_date",
                        "accommodation",
                        "diet",
                        "looking_forward_to_you",
                        "total_working_days",
                        "total_participants",
                        "total_participants_under_26",
                        "contact_person_name",
                        "contact_person_telephone",
                        "contact_person_email",
                        "comment_on_work_done",
                        "other_work",
                    ],
                }
            ),
        }

    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION

    def add_view(self, request, extra_context=None, **kwargs):
        extra_context = self._extra_view_context()
        return super().add_view(request, extra_context=extra_context, **kwargs)

    def change_view(self, request, object_id, extra_context=None, **kwargs):
        extra_context = self._extra_view_context()
        return super().change_view(
            request, object_id, extra_context=extra_context, **kwargs
        )

    def sum_yield_amount(self, obj):
        return obj.sum_yield_amount

    sum_yield_amount.short_description = _("Yield per period")

    def go_to_users(self, obj):
        """
        Provides link for each row with the Event ID to UserProfiles.
        The ID is used then to filter Users, which are related to the Event.
        """
        url = reverse_lazy("admin:aklub_userprofile_changelist")
        url_with_querystring = f"{url}?event-of-interaction-id={obj.id}"

        return mark_safe(f"<a href='{url_with_querystring}'>Show users</a>")

    def _get_unique_organizator_interaction(self, organizators):
        organizators_with_interaction = []
        for organizator in organizators:
            if organizator["id"] not in [
                o["id"] for o in organizators_with_interaction
            ]:
                organizators_with_interaction.append(
                    {
                        "id": organizator["id"],
                        "has_any_coordinator": organizator["has_any_coordinator"],
                    }
                )
            else:
                if organizator["has_any_coordinator"] == self.yes_icon:
                    organizators_with_interaction[-1][
                        "has_any_coordinator"
                    ] = organizator["has_any_coordinator"]
        return organizators_with_interaction

    def local_organizer(self, obj):
        names = []
        for profile in obj.organization_team.all():
            if profile.is_userprofile():
                names.append(
                    "{first_name} {last_name}".format(
                        first_name=profile.first_name.strip(),
                        last_name=profile.last_name.strip(),
                    )
                )
            else:
                names.append(profile.name)

        return mark_safe("<br>".join(names)) if names else self.none_val

    local_organizer.short_description = _("Local organizer")
    local_organizer.admin_order_field = "local_organizer"

    def main_coordinator(self, obj):
        """Return the user who created the event"""
        names = []
        event_creators = OrganizationTeam.objects.filter(
            event=obj,
            position__name="Event creator",
        )
        for creator in event_creators:
            if creator.profile.is_userprofile():
                names.append(
                    "<b>{first_name} {last_name}</b>".format(
                        first_name=creator.profile.first_name.strip(),
                        last_name=creator.profile.last_name.strip(),
                    )
                )
            else:
                names.append(creator.profile.get_main_contact_name())

        return mark_safe("<br>".join(names)) if names else self.none_val

    main_coordinator.short_description = _("Event creator")
    main_coordinator.admin_order_field = "main_coordinator"

    def main_coordinator_email(self, obj):
        """Return the email of the user who created the event"""
        emails = []
        event_creators = OrganizationTeam.objects.filter(
            event=obj,
            position__name="Event creator",
        )
        for creator in event_creators:
            emails.append(creator.profile.get_email())

        return mark_safe("<br>".join(emails)) if emails else self.none_val

    main_coordinator_email.short_description = _("Event creator email")
    main_coordinator_email.admin_order_field = "main_coordinator_email"

    def secondary_coordinator_email(self, obj):
        """Return empty for secondary coordinator (not used for event creator)"""
        return self.none_val

    secondary_coordinator_email.short_description = _("Contact person secondary email")
    secondary_coordinator_email.admin_order_field = "secondary_coordinator_email"

    def main_coordinator_telephone(self, obj):
        """Return the telephone of the user who created the event"""
        telephones = []
        event_creators = OrganizationTeam.objects.filter(
            event=obj,
            position__name="Event creator",
        )
        for creator in event_creators:
            telephones.append(creator.profile.get_telephone())

        return mark_safe("<br>".join(telephones)) if telephones else self.none_val

    main_coordinator_telephone.short_description = _("Event creator telephone")
    main_coordinator_telephone.admin_order_field = "main_coordinator_telephone"

    def get_program_items(self, obj):
        """Return program items (child events/descendants)"""
        if not obj:
            return "-"
        
        program_items = obj.tn_children.all().order_by("datetime_from")
        if not program_items.exists():
            return "-"
        
        items = []
        for item in program_items:
            item_info = f"<b>{item.name}</b>"
            if item.datetime_from:
                item_info += f": {item.datetime_from.strftime('%H:%M')}"
            if item.datetime_to:
                item_info += f" - {item.datetime_to.strftime('%H:%M')}"
            if item.description:
                item_info += f"<br/>{item.description[:100]}..."
            items.append(item_info)
        
        return mark_safe("<br/><br/>".join(items))
    
    get_program_items.short_description = _("Program Items")

    def get_organizers(self, obj):
        """Return all organizers"""
        if not obj:
            return "-"
        
        organizers = []
        for profile in obj.organization_team.all():
            if profile.is_userprofile():
                name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
                if name:
                    organizers.append(name)
            elif hasattr(profile, 'name') and profile.name:
                organizers.append(profile.name)
        
        return ", ".join(organizers) if organizers else "-"
    
    get_organizers.short_description = _("Organizers")
    get_organizers.readonly = True

    def get_company(self, obj):
        """Return company information if linked to the event"""
        if not obj:
            return "-"
        
        from aklub.models import CompanyProfile
        
        org_team = (
            OrganizationTeam.objects.select_related("profile")
            .filter(
                event=obj,
                profile__polymorphic_ctype__model=CompanyProfile._meta.model_name,
            )
            .first()
        )
        
        if not org_team:
            return "-"
        
        company = org_team.profile
        company_info = []
        if hasattr(company, 'name') and company.name:
            company_info.append(f"<b>{company.name}</b>")
        if hasattr(company, 'crn') and company.crn:
            company_info.append(f"CRN: {company.crn}")
        if hasattr(company, 'tin') and company.tin:
            company_info.append(f"TIN: {company.tin}")
        if hasattr(company, 'type') and company.type:
            company_info.append(f"Type: {company.type.type}")
        
        return mark_safe("<br/>".join(company_info)) if company_info else "-"
    
    get_company.short_description = _("Company")
    get_company.readonly = True

    def has_any_coordinator_interaction_with_organize_zmj(
        self,
        obj,
        interaction_type_name=_("Organizace lokality Zažít město jinak"),
        then=None,
    ):
        if then is None:
            then = Value(self.yes_icon)
        whens = [
            When(
                profile__interaction__type__name=interaction_type_name,
                then=then,
            ),
        ]
        organizators = (
            OrganizationTeam.objects.filter(
                event=obj,
                position__name__in=(
                    self.main_coordinator_name,
                    self.secondary_coordinator_name,
                ),
            )
            .annotate(
                has_any_coordinator=Case(
                    *whens,
                    output_field=CharField(),
                    default=Value(self.no_icon),
                )
            )
            .values()
        )

        return (
            mark_safe(
                "<br>".join(
                    [
                        i["has_any_coordinator"]
                        for i in self._get_unique_organizator_interaction(organizators)
                    ]
                )
            )
            if organizators
            else self.none_val
        )

    has_any_coordinator_interaction_with_organize_zmj.short_description = _(
        "Have any interaction with organize location ZMJ"
    )
    has_any_coordinator_interaction_with_organize_zmj.admin_order_field = (
        "has_any_coordinator_interaction_with_organize_zmj"
    )

    def is_in_location(self, obj, location=_("praha")):
        if obj.location and obj.location.specific_name:
            return location in obj.location.specific_name.lower()
        return None

    is_in_location.short_description = _("Is in the Prague")
    is_in_location.admin_order_field = "is_in_location"
    is_in_location.boolean = True

    def specific_location_name(self, obj):
        return obj.location.name if obj.location else None

    specific_location_name.short_description = _("Specific location name")
    specific_location_name.admin_order_field = "specific_location_name"

    def has_any_coordinator_interaction_with_organize_uso(
        self,
        obj,
        interaction_type_name=_("Účast na setkání organizátorů"),
    ):
        return self.has_any_coordinator_interaction_with_organize_zmj(
            obj,
            interaction_type_name,
        )

    has_any_coordinator_interaction_with_organize_uso.short_description = _(
        "Have any interaction with Účast na setkání organizátorů"
    )
    has_any_coordinator_interaction_with_organize_uso.admin_order_field = (
        "has_any_coordinator_interaction_with_organize_uso"
    )

    def has_any_coordinator_interaction_type_of_contract_with_signed_result(
        self,
        obj,
        interaction_type_name=_("Smlouva"),
        interaction_result_name=_("Podepsáno"),
    ):
        whens = [
            When(
                profile__interaction__type__name=interaction_type_name,
                profile__interaction__result__name=interaction_result_name,
                then=Value(self.yes_icon),
            ),
        ]
        organizators = (
            OrganizationTeam.objects.filter(
                event=obj,
                position__name__in=(
                    self.main_coordinator_name,
                    self.secondary_coordinator_name,
                ),
            )
            .annotate(
                has_any_coordinator=Case(
                    *whens,
                    output_field=CharField(),
                    default=Value(self.no_icon),
                )
            )
            .values()
        )

        return (
            mark_safe(
                "<br>".join(
                    [
                        i["has_any_coordinator"]
                        for i in self._get_unique_organizator_interaction(organizators)
                    ]
                )
            )
            if organizators
            else self.none_val
        )

    has_any_coordinator_interaction_type_of_contract_with_signed_result.short_description = _(
        "Has any interaction with type of contract with signed result"
    )
    has_any_coordinator_interaction_type_of_contract_with_signed_result.admin_order_field = (
        "has_any_coordinator_interaction_type_of_contract_with_signed_result"
    )

    def has_any_coordinator_interaction_type_of_order_signs(
        self,
        obj,
        interaction_type_name=_("Objednal značky"),
    ):
        return self.has_any_coordinator_interaction_with_organize_zmj(
            obj,
            interaction_type_name,
            then=Concat(
                Value(self.yes_icon),
                Value(" "),
                F("profile__interaction__status"),
            ),
        )

    has_any_coordinator_interaction_type_of_order_signs.short_description = _(
        "Has any interaction with type of order signs"
    )
    has_any_coordinator_interaction_type_of_order_signs.admin_order_field = (
        "has_any_coordinator_interaction_type_of_order_signs"
    )

    def has_any_coordinator_interaction_type_of_zabor_zmj(
        self,
        obj,
        interaction_type_name=_("Zábor ZMJ"),
    ):
        return self.has_any_coordinator_interaction_with_organize_zmj(
            obj,
            interaction_type_name,
            then=Concat(
                Value(self.yes_icon),
                Value(" "),
                F("profile__interaction__status"),
            ),
        )

    has_any_coordinator_interaction_type_of_zabor_zmj.short_description = _(
        "Has any interaction with type of Zábor ZMJ"
    )
    has_any_coordinator_interaction_type_of_zabor_zmj.admin_order_field = (
        "has_any_coordinator_interaction_type_of_zabor_zmj"
    )

    def get_changelist(self, request, **kwargs):
        return EventChangeList

    def get_changelist_form(self, request, **kwargs):
        return EventChangeListForm

    def save_model(self, request, obj, form, change):
        # Save ManyToManyField Event
        if "event" in form.changed_data:
            obj.event.set(form.cleaned_data["event"])
        super().save_model(request, obj, form, change)
