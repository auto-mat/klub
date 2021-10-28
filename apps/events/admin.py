import datetime

from aklub import darujme
from aklub.filters import unit_admin_mixin_generator

from api.serializers import EventSerializer

from django.contrib import admin
from django.db.models import Q, Sum
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

from . import filters
from .forms import EventForm
from .models import (
    Event,
    EventType,
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


@admin.register(OrganizationPosition)
class OrganizationPositionAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "place", "region", "gps_latitude", "gps_longitude")


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(Qualification)
class Qualificationdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviated_name")


class OrganizationTeamInline(admin.TabularInline):
    model = OrganizationTeam
    autocomplete_fields = ["profile"]
    classes = ["collapse"]
    extra = 0


@admin.register(Event)
class EventAdmin(unit_admin_mixin_generator("administrative_units"), admin.ModelAdmin):
    form = EventForm
    inlines = (OrganizationTeamInline,)
    list_display = (
        "name",
        "id",
        "slug",
        "date_from",
        "date_to",
        "sum_yield_amount",
        "number_of_members",
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
    list_filter = [
        ("donorpaymentchannel__payment__date", filters.EventYieldDateRangeFilter),
        "grant",
    ]
    readonly_fields = (
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
    actions = (download_darujme_statement,)
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
                    ("date_from", "date_to", "start_date"),
                    "variable_symbol_prefix",
                    "description",
                    "administrative_units",
                ),
            },
        ),
        (
            _("Detail information"),
            {
                "classes": ("collapse",),
                "fields": (
                    ("age_from", "age_to"),
                    "event_type",
                    "program",
                    "indended_for",
                    "location",
                    "responsible_person",
                    "registration_method",
                    "participation_fee",
                    "meeting",
                    "is_internal",
                    "focus_on_members",
                    "note",
                    "result",
                    "number_of_actions",
                    "promoted_in_magazine",
                    "vip_action",
                    "total_working_days",
                    "working_hours",
                    "accommodation",
                    "diet",
                    "looking_forward_to_you",
                    "contact_person_name",
                    "contact_person_email",
                    "contact_person_telephone",
                    "comment_on_work_done",
                    "other_work",
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
            _("Additional information"),
            {
                "classes": ("collapse",),
                "fields": (
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
                ),
            },
        ),
        (
            _("Statistics"),
            {
                "classes": ("collapse",),
                "fields": (
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
                ),
            },
        ),
    )

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
        }

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
        url_with_querystring = f'{url}?event-of-interaction-id={obj.id}'

        return mark_safe(f"<a href='{url_with_querystring}'>Show users</a>")