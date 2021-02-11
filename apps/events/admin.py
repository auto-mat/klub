import datetime

from aklub import darujme
from aklub.filters import unit_admin_mixin_generator

from django.contrib import admin
from django.db.models import Q, Sum
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from . import filters
from .forms import EventForm
from .models import Event, EventType, Location, OrganizationPosition, OrganizationTeam, OrganizingAssociation


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


@admin.register(OrganizingAssociation)
class OrganizingAssociationAdmin(admin.ModelAdmin):
    pass


@admin.register(OrganizationPosition)
class OrganizationPositionAdmin(admin.ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


class OrganizationTeamInline(admin.TabularInline):
    model = OrganizationTeam
    autocomplete_fields = ['profile']
    classes = ['collapse']


@admin.register(Event)
class EventAdmin(unit_admin_mixin_generator('administrative_units'), admin.ModelAdmin):
    form = EventForm
    inlines = (OrganizationTeamInline,)
    list_display = (
        'name',
        'id',
        'slug',
        'date_from',
        'date_to',
        'sum_yield_amount',
        'number_of_members',
        'number_of_recruiters',
        'yield_total',
        'total_expenses',
        'expected_monthly_income',
        'return_of_investmensts',
        'average_yield',
        'average_expense',
    )
    list_filter = [
        ('donorpaymentchannel__payment__date', filters.EventYieldDateRangeFilter),
    ]
    readonly_fields = (
        'number_of_members',
        'number_of_recruiters',
        'yield_total',
        'total_expenses',
        'expected_monthly_income',
        'return_of_investmensts',
        'average_yield',
        'average_expense',
    )
    search_fields = ('name', )
    actions = (download_darujme_statement,)
    save_as = True

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'slug',
                'basic_purpose',
                'grant',
                ('date_from', 'date_to'),
                'variable_symbol_prefix',
                'description',
                'result',
                'administrative_units',


            ),
        }),
        (_('Detail information'), {
            'classes': ('collapse',),
            'fields': (
                ('age_from', 'age_to'),
                'event_type', 'program', 'indended_for',
                'participation_fee', 'meeting', 'is_internal', 'focus_on_members',
                'note',
            ),
        }),
        (_('Web setting'), {
            'classes': ('collapse',),
            'fields': (
                'enable_signing_petitions', 'enable_registration', 'allow_statistics', 'public_on_web',
                'email_confirmation_redirect', 'entry_form_url'
            ),
        }),
        (_('Statistics'), {
            'classes': ('collapse',),
            'fields': (
                'number_of_members', 'number_of_recruiters', 'yield_total',
                'total_expenses', 'expected_monthly_income', 'return_of_investmensts',
                'average_yield', 'average_expense',
            ),
        }),
    )

    def get_queryset(self, request):
        donor_filter = {}
        extra_filters = request.GET
        dpd_gte = extra_filters.get('donorpaymentchannel__payment__date__range__gte')
        dpd_lte = extra_filters.get('donorpaymentchannel__payment__date__range__lte')
        if dpd_gte:
            donor_filter['donorpaymentchannel__payment__date__gte'] = datetime.datetime.strptime(dpd_gte, '%d.%m.%Y')
        if dpd_lte:
            donor_filter['donorpaymentchannel__payment__date__lte'] = datetime.datetime.strptime(dpd_lte, '%d.%m.%Y')
        queryset = super().get_queryset(request).annotate(
            sum_yield_amount=Sum('donorpaymentchannel__payment__amount', filter=Q(**donor_filter)),
        )
        return queryset

    def sum_yield_amount(self, obj):
        return obj.sum_yield_amount

    sum_yield_amount.short_description = _("Yield per period")
