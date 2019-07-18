# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
#
# Copyright (C) 2010 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Definition of administration interface for club management application"""

import copy
import datetime

from adminactions import actions, merge

from adminfilters.filters import RelatedFieldCheckBoxFilter

from advanced_filters.admin import AdminAdvancedFiltersMixin

from daterange_filter.filter import DateRangeFilter

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import site
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import CharField, Sum
from django.http import HttpResponseRedirect
from django.utils.html import format_html, format_html_join, mark_safe
from django.utils.translation import ugettext as _

try:
    from django.urls import reverse
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse

from import_export import fields, widgets
from import_export.admin import ImportExportMixin
from import_export.resources import ModelResource

import large_initial

import nested_admin

from related_admin import RelatedFieldAdmin

from smmapdfs.actions import make_pdfsandwich
from smmapdfs.admin_abcs import PdfSandwichAdmin, PdfSandwichFieldAdmin

from . import darujme, filters, mailing, tasks
from .filters import unit_admin_mixin_generator
from .forms import UserCreateForm, UserUpdateForm
from .models import (
    AccountStatements, AdministrativeUnit, AutomaticCommunication, BankAccount, Condition, DonorPaymentChannel,
    Event, Expense, Interaction, MassCommunication, NewUser, Payment, Recruiter,
    Result, Source, TaxConfirmation, TaxConfirmationField,
    TaxConfirmationPdf, Telephone, TerminalCondition, UserBankAccount,
    UserProfile, UserYearPayments,
)


def admin_links(args_generator):
    return format_html_join(
        mark_safe('<br/>'),
        '<a href="{}">{}</a>',
        args_generator,
    )


# -- INLINE FORMS --
class PaymentsInline(nested_admin.NestedTabularInline):
    readonly_fields = ('account_statement',)
    exclude = ('user',)
    model = Payment
    extra = 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('account_statement')
        return qs


class DonorPaymentChannelInline(nested_admin.NestedStackedInline):
    model = DonorPaymentChannel
    extra = 0
    can_delete = True
    show_change_link = True
    inlines = [PaymentsInline]
    autocomplete_fields = ('event',)

    fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                ('bank_account', 'user_bank_account', 'regular_payments',),
            ),
        }),
        (_('Details'), {
            'classes': ('collapse',),
            'fields': [
                ('VS'),
                ('registered_support', 'regular_amount', 'regular_frequency'),
                ('expected_date_of_first_payment', 'exceptional_membership'),
                ('other_support'),
                ('event'),
            ],
        }
         )
    )

    # filter_horizontal = ('event', )


class PaymentsInlineNoExtra(PaymentsInline):

    raw_id_fields = ('user_donor_payment_channel',)
    fields = (
        'type',
        'user_donor_payment_channel',
        'user_identification',
        'account_name',
        'recipient_message',
        'bank_name',
        'date',
        'amount',
        'account',
        'bank_code',
        'VS',
        'VS2',
        'SS',
        'KS',
        'BIC',
        'transfer_type',
        'transfer_note',
        'currency',
        'done_by',
        'specification',
        'order_id',
    )
    extra = 0

    def user__campaign(self, obj):
        return obj.user.campaign


class InteractionInline(nested_admin.NestedTabularInline):
    model = Interaction
    extra = 0
    can_delete = True
    show_change_link = True
    readonly_fields = ('type', 'created_by', 'handled_by')
    fk_name = 'user'

    def get_queryset(self, request):
        qs = super(InteractionInline, self).get_queryset(request)
        qs = qs.filter(type__in=('individual', 'auto')).order_by('-date')
        qs = qs.select_related('created_by', 'handled_by')
        return qs


class ExpenseInline(admin.TabularInline):
    model = Expense


def show_payments_by_year(self, request, queryset):
    payments = Payment.objects.filter(user_donor_payment_channel__in=queryset)
    payment_dates = payments.dates('date', 'year')
    amount_string = [
        "%s: %s" % (
            date_year.year,
            payments.filter(date__year=date_year.year).aggregate(Sum('amount'))['amount__sum'],
        ) for date_year in payment_dates]
    amount_string += (_("TOT.: %s") % payments.aggregate(Sum('amount'))['amount__sum'],)
    self.message_user(request, mark_safe("<br/>".join(amount_string)))


show_payments_by_year.short_description = _("Show payments by year")


def send_mass_communication_action(self, request, queryset, distinct=False):
    """Mass communication action

    Determine the list of user ids from the associated
    queryset and redirect us to insert form for mass communications
    with the send_to_users M2M field prefilled with these
    users."""
    if queryset.model is UserProfile:
        queryset = DonorPaymentChannel.objects.filter(user__in=queryset)
    if distinct:
        queryset = queryset.order_by('user__id').distinct('user')
    redirect_url = large_initial.build_redirect_url(
        request,
        "admin:aklub_masscommunication_add",
        params={'send_to_users': queryset},
    )
    return HttpResponseRedirect(redirect_url)


send_mass_communication_action.short_description = _("Send mass communication")


def send_mass_communication_distinct_action(self, req, queryset, distinct=False):
    return send_mass_communication_action(self, req, queryset, True)


send_mass_communication_distinct_action.short_description = _("Send mass communication withoud duplicities")


class UserProfileResource(ModelResource):
    class Meta:
        model = UserProfile
        exclude = ('id',)
        import_id_fields = ('email', )
        import_id_field = 'email'

    telephone = fields.Field()
    VS = fields.Field()

    def import_obj(self, obj, data, dry_run):  # noqa
        bank_account = BankAccount.objects.all().first()

        if not data.get("username"):
            data["username"] = None
        if data.get('telephone'):
            obj.save()
            telephone, _ = Telephone.objects.get_or_create(telephone=data['telephone'], user=obj, defaults={'is_primary': None})

        if data.get('donor'):
            if data.get('VS'):
                VS = data['VS']
            else:
                from .views import generate_variable_symbol
                VS = generate_variable_symbol()
            obj.save()
            donors, _ = DonorPaymentChannel.objects.get_or_create(
                VS=VS,
                user=obj,
                defaults={'bank_account': bank_account},
            )
            if data.get('bank_account'):
                bank_account, _ = BankAccount.objects.get_or_create(bank_account_number=data['bank_account'])
                donors.bank_account = bank_account
                donors.save()
            if data.get('user_bank_account'):
                user_bank_account, _ = UserBankAccount.objects.get_or_create(bank_account_number=data['user_bank_account'])
                donors.user_bank_account = user_bank_account
                donors.save()
            if data.get('event'):
                event, _ = Event.objects.get_or_create(name=data['event'])
                donors.event.add(event)
                donors.user = obj
                donors.save()

        if data.get("email"):
            super(UserProfileResource, self).import_obj(obj, data, dry_run)
            if data.get("administrative_units"):
                obj.save()
                user = UserProfile.objects.get(email=data["email"])
                for unit in list(data["administrative_units"].replace(",", "")):
                    administrate_unit = AdministrativeUnit.objects.get(pk=unit)
                    user.administrative_units.add(administrate_unit)
                    user.save()

                obj.save()
                user = UserProfile.objects.get(email=obj.email)
                administrated_unit = AdministrativeUnit.objects.get(pk=data["administrated_units"])
                user.administrated_units.add(administrated_unit)
                user.save()
        else:
            data["email"] = None
            super(UserProfileResource, self).import_obj(obj, data, dry_run)

    def dehydrate_telephone(self, profile):
        return profile.get_telephone()

    def dehydrate_VS(self, profile):
        return profile.get_donor()

    def before_import_row(self, row, **kwargs):
        row['email'] = row['email'].lower()

    def import_field(self, field, obj, data, is_m2m=False):
        if field.attribute and field.column_name in data and not getattr(obj, field.column_name):
            field.save(obj, data, is_m2m)


class UserProfileMergeForm(merge.MergeForm):
    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields['sex'].required = False
        return ret_val

    class Meta:
        model = UserProfile
        fields = '__all__'


class TelephoneInline(nested_admin.NestedTabularInline):
    model = Telephone
    extra = 0
    can_delete = True
    show_change_link = True


class BankAccountAdmin(unit_admin_mixin_generator('administrative_unit'), admin.ModelAdmin):
    model = BankAccount

    list_fields = (
        'bank_account', 'bank_account_number', 'administrative_unit',
    )

    search_fields = (
        'bank_account', 'bank_account_number',
    )

    list_filter = (
        'bank_account', 'bank_account_number',
    )


class UserBankAccountAdmin(admin.ModelAdmin):
    model = UserBankAccount

    search_fields = (
        'bank_account', 'bank_account_number',
    )

    list_filter = (
        'bank_account', 'bank_account_number',
    )


class UserProfileAdmin(
    filters.AdministrativeUnitAdminMixin,
    ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin,
    UserAdmin, nested_admin.NestedModelAdmin,
):
    resource_class = UserProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    merge_form = UserProfileMergeForm
    add_form = UserCreateForm
    form = UserUpdateForm

    list_display = (
        'person_name',
        'email',
        'addressment',
        'get_addressment',
        'get_last_name_vokativ',
        'get_main_telephone',
        'title_before',
        'title_after',
        'sex',
        'is_staff',
        'registered_support_date',
        'event',
        'variable_symbol',
        'regular_payments_info',
        'regular_amount',
        'date_joined',
        'last_login',
    )

    advanced_filter_fields = (
        'email',
        'addressment',
        'telephone__telephone',
        'title_before',
        'first_name',
        'last_name',
        'title_after',
        'sex',
        'is_staff',
        'date_joined',
        'last_login',
        ('userincampaign__campaign__name', _("Jméno kampaně")),
    )
    list_editable = (
        'addressment',
    )
    search_fields = (
        'email',
        'title_before',
        'first_name',
        'last_name',
        'title_after',
        'telephone__telephone',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'language',
        'userincampaign__campaign',
        filters.RegularPaymentsFilter,
        filters.EmailFilter,
        filters.TelephoneFilter,
        filters.NameFilter,
    )

    add_fieldsets = (
        (_('Personal data'), {
            'classes': ('wide',),
            'fields': (
                'username', ('first_name', 'last_name'), 'email', 'sex',
                ('birth_day', 'birth_month', 'age_group'),
                'administrative_units',
            ),
        }),
    )

    edit_fieldsets = (
        (_('Personal data'), {
            'classes': ('wide',),
            'fields': (
                'username', ('first_name', 'last_name'), ('title_before', 'title_after'), 'email', 'sex',
                ('birth_day', 'birth_month', 'age_group'),
                'get_main_telephone',
                'note',
                'administrative_units',
            ),
        }),
        (_('Contact data'), {
            'classes': ('wide', ),
            'fields': [
                ('street', 'city',),
                ('country', 'zip_code'),
                'different_correspondence_address',
                ('addressment', 'addressment_on_envelope'),
            ],
        }
         ),
        ('Preferences', {
            'fields': (
                ('public', 'send_mailing_lists', ),
                ('newsletter_on', 'call_on', ),
                ('challenge_on', 'letter_on', ),
            ),
        })
    )

    superuser_fieldsets = (
        (_('Rights and permissions'), {
            'classes': ('collapse',),
            'fields': [
                ('password',),
                ('is_staff', 'is_superuser'),
                'groups',
                'administrated_units',
            ],
        }
        ),
    )

    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    def get_details(self, obj, attr, *args):
        return [f[attr] for f in list(obj.values(attr)) if f[attr] is not None]

    def date_format(self, obj):
        return list(map(lambda o: o.strftime('%d. %m. %Y'), obj))

    def registered_support_date(self, obj):
        result = self.get_details(obj.userchannels.all(), "registered_support")
        return self.date_format(result)

    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'registered_support'

    def event(self, obj):
        result = UserProfile.objects.get(id=obj.id)
        donors = result.userchannels.select_related().all()
        return [e.event for e in donors]

    event.short_description = _("Event")
    event.admin_order_field = 'event'

    def variable_symbol(self, obj):
        return self.get_details(obj.userchannels.all(), "VS")

    variable_symbol.short_description = _("VS")
    variable_symbol.admin_order_field = 'variable_symbol'

    def regular_payments_info(self, obj):
        return self.get_details(obj.userchannels.all(), "regular_payments")

    regular_payments_info.short_description = _("Regular payment info")
    regular_payments_info.admin_order_field = 'regular_payments_info'

    def regular_amount(self, obj):
        return self.get_details(obj.userchannels.all(), "regular_amount")

    regular_amount.short_description = _("Regular amount")
    regular_amount.admin_order_field = 'regular_amount'

    readonly_fields = ('userattendance_links', 'date_joined', 'last_login', 'get_main_telephone')
    actions = (send_mass_communication_distinct_action,)
    inlines = [TelephoneInline, DonorPaymentChannelInline, InteractionInline]

    def get_fieldsets(self, request, obj=None):
        if obj:
            fieldsets = self.edit_fieldsets
        else:
            fieldsets = self.add_fieldsets
        if request.user.is_superuser and self.superuser_fieldsets:
            return fieldsets + self.superuser_fieldsets
        else:
            return fieldsets
        super().get_fieldsets(request, obj)

    def save_formset(self, request, form, formset, change):
        if not issubclass(formset.model, DonorPaymentChannel):
            return super().save_formset(request, form, formset, change)
        formset.save()
        for f in formset.forms:
            obj = f.instance
            obj.generate_VS()


class DonorPaymentChannelResource(ModelResource):
    user_email = fields.Field(
        column_name='user_email',
        attribute='user',
        widget=widgets.ForeignKeyWidget(UserProfile, 'email'),
    )

    class Meta:
        model = DonorPaymentChannel
        fields = (
            'id',
            'event',
            'user',
            'user__title_before',
            'user__first_name',
            'user__last_name',
            'user__title_after',
            'user__sex',
            # 'userprofile__telephone',
            'user_email',
            'user__street',
            'user__city',
            'user__zip_code',
            'VS',
            'user__club_card_available',
            # 'wished_information',
            'regular_payments',
            'regular_frequency',
            'registered_support',
            # 'note',
            # 'additional_information',
            'user__is_active',
            'user__language',
            # 'expected_regular_payment_date',
            # 'expected_regular_payment_date',
            'extra_money',
            'number_of_payments',
            'payment_total',
            'regular_amount',
            'last_payment_date',
        )
        export_order = fields
        import_id_fields = ('user_email', 'campaign')

    last_payment_date = fields.Field()

    def dehydrate_last_payment_date(self, user_in_campaign):
        return user_in_campaign.last_payment_date()


# -- ADMIN FORMS --
class DonorPaymethChannelAdmin(
    unit_admin_mixin_generator('user__administrative_units'),
    ImportExportMixin,
    AdminAdvancedFiltersMixin,
    RelatedFieldAdmin,
):
    list_display = (
        'person_name',
        'user__email',
        # 'user__telephone_url',
        # 'source',
        'event',
        'VS',
        # 'registered_support_date',
        # 'regular_payments_info',
        # 'payment_delay',
        # 'extra_payments',
        # 'number_of_payments',
        # 'total_contrib_string',
        'regular_amount',
        # 'next_communication_date',
        # 'next_communication_method',
        'user__is_active',
        # 'last_payment_date',
        # 'email_confirmed',
    )
    advanced_filter_fields = (
        'user__first_name',
        'user__last_name',
        'user__email',
        # 'user__telephone',
        # 'source',
        ('campaign__name', _("Campaign name")),
        'VS',
        'registered_support',
        'regular_payments',
        'extra_money',
        'number_of_payments',
        'payment_total',
        'regular_amount',
        # 'next_communication_date',
        # 'next_communication_method',
        'user__is_active',
        'last_payment__date',
    )
    date_hierarchy = 'registered_support'
    list_filter = [
        'regular_payments',
        'user__language',
        'user__is_active',
        # 'wished_information',
        'old_account',
        # 'email_confirmed',
        # 'source',
        ('event', RelatedFieldCheckBoxFilter),
        ('registered_support', DateRangeFilter),
        filters.UserConditionFilter, filters.UserConditionFilter1,
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'VS',
        'user__email',
        # 'user__telephone',
    ]
    ordering = ('user__last_name',)
    actions = (
        send_mass_communication_action,
        send_mass_communication_distinct_action,
        show_payments_by_year,
    )
    resource_class = DonorPaymentChannelResource
    save_as = True
    list_max_show_all = 10000
    list_per_page = 100
    # inlines = [PaymentsInline, InteractionInline]
    raw_id_fields = (
        'user',
        # 'recruiter',
    )
    readonly_fields = (
        # 'verified_by',
        'user_telephone_url',
        'user_note',
    )
    fieldsets = [
        (_('Basic personal'), {
            'fields': [
                ('event', 'user'),
                ('user_telephone_url',),
                ('user_note',),
            ],
        }),
        (_('Additional'), {
            'fields': [
                # 'knows_us_from',
                # 'why_supports',
                # 'field_of_work',
                # 'additional_information',
            ],
            'classes': ['collapse'],
        }),
        (_('Support'), {
            'fields': [
                'VS',
                'registered_support',
                (
                    'regular_payments', 'regular_frequency',
                    'regular_amount', 'expected_date_of_first_payment',
                    'exceptional_membership'
                ),
                'other_support', 'old_account',
            ],
        }),
        (_('Communications'), {
            'fields': [
                # 'wished_information',
                # 'wished_tax_confirmation',
                # 'wished_welcome_letter',
                # 'email_confirmed',
                # 'public',
                # 'gdpr_consent',
                (
                    # 'next_communication_date',
                    # 'next_communication_method',
                ),
            ],
            'classes': ['collapse'],
        }),
        (_('Notes'), {
            'fields': [
                # 'note',
                # 'source',
                # 'verified',
                # 'verified_by',
                # 'activity_points',
                # 'recruiter',
            ],
            'classes': ['collapse'],
        }),
    ]

    def user_note(self, obj):
        return obj.user.note

    def user_telephone_url(self, obj):
        return obj.user.telephone_url()

    def save_formset(self, request, form, formset, change):
        # We need to save the request.user to inline Communication
        # the same as we do in CommunicationAdmin.save_model().
        # Unfortunatelly, save_model() doesn't work on CommunicationInline
        # so we need to workaround it using save_formset here.
        if not issubclass(formset.model, Interaction):
            return super().save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.created_by = request.user
            instance.handled_by = request.user
            instance.save()
        formset.save_m2m()

    # def save_model(self, request, obj, form, change):
    #     if obj.verified and not obj.verified_by:
    #         obj.verified_by = request.user
    #     obj.save()


class UserYearPaymentsAdmin(DonorPaymethChannelAdmin):
    list_display = (
        'person_name',
        'user__email',
        # 'source',
        'VS',
        # 'registered_support_date',
        'payment_total_by_year',
        'user__is_active',
        # 'last_payment_date',
    )
    list_filter = [
        ('payment__date', DateRangeFilter), 'regular_payments', 'user__language', 'user__is_active',
        # 'wished_information',
        'old_account',
        # 'source',
        ('registered_support', DateRangeFilter), filters.UserConditionFilter, filters.UserConditionFilter1,
    ]

    def payment_total_by_year(self, obj):
        if self.from_date and self.to_date:
            return obj.payment_total_range(
                datetime.datetime.strptime(self.from_date, '%d.%m.%Y'),
                datetime.datetime.strptime(self.to_date, '%d.%m.%Y'),
            )

    def changelist_view(self, request, extra_context=None):
        self.from_date = request.GET.get('drf__payment__date__gte', None)
        self.to_date = request.GET.get('drf__payment__date__lte', None)
        return super(UserYearPaymentsAdmin, self).changelist_view(request, extra_context=extra_context)


class PaymentAdmin(
    unit_admin_mixin_generator('user_donor_payment_channel__user__administrative_units'),
    ImportExportMixin,
    RelatedFieldAdmin,
):
    list_display = (
        'id',
        'date',
        'user_donor_payment_channel__event',
        'account_statement',
        'amount',
        'person_name',
        'account_name',
        'account',
        'bank_code',
        "transfer_note",
        "currency",
        "recipient_message",
        "operation_id",
        "transfer_type",
        "specification",
        "order_id",
        'VS',
        'VS2',
        'SS',
        'user_identification',
        'type',
        'paired_with_expected',
        'created',
        'updated',
    )
    fieldsets = [
        (_("Basic"), {
            'fields': [
                'user_donor_payment_channel', 'date', 'amount',
                ('type',),
            ],
        }),
        (_("Details"), {
            'fields': [
                'account',
                'bank_code',
                'account_name',
                'bank_name',
                'VS',
                'VS2',
                'KS',
                'SS',
                'BIC',
                'user_identification',
                'account_statement',
                'done_by',
                'transfer_note',
                'currency',
                'recipient_message',
                'operation_id',
                'transfer_type',
                'specification',
                'order_id',
                'created',
                'updated',
            ],
        }),
    ]
    readonly_fields = (
        'BIC',
        'KS',
        'SS',
        'VS',
        'VS2',
        'account',
        'account_name',
        'account_statement',
        'bank_code',
        'bank_name',
        'currency',
        'operation_id',
        'order_id',
        'recipient_message',
        'specification',
        'transfer_note',
        'transfer_type',
        'user_identification',
        'done_by',
        'updated',
        'account_statement',
        'created',
    )
    raw_id_fields = ('user_donor_payment_channel',)
    list_filter = ['type', 'date', filters.PaymentsAssignmentsFilter]
    date_hierarchy = 'date'
    search_fields = [
        'user_donor_payment_channel__user__last_name',
        'user_donor_payment_channel__user__first_name',
        'amount',
        'VS',
        'SS',
        'user_identification',
    ]
    list_max_show_all = 10000


class NewUserAdmin(DonorPaymethChannelAdmin):
    list_display = (
        'person_name',
        # 'is_direct_dialogue',
        'VS',
        'regular_payments',
        'registered_support',
        # 'recruiter',
        'user__is_active',
    )


class InteractionAdmin(
    unit_admin_mixin_generator('user__administrative_units'),
    RelatedFieldAdmin,
    admin.ModelAdmin,
):
    list_display = (
        'subject',
        'dispatched',
        'user',
        'event',
        # 'user__telephone__telephone',
        # 'user__next_communication_date',
        'method',
        'result',
        'created_by',
        'handled_by',
        # 'user__regular_payments_info',
        # 'user__payment_delay',
        # 'user__extra_payments',
        'date', 'type',
    )
    autocomplete_fields = ('user', 'event')
    readonly_fields = ('type', 'created_by', 'handled_by', )
    list_filter = ['dispatched', 'send', 'date', 'method', 'type', 'event']
    search_fields = (
        'subject',
        # 'user__userprofile__telephone',
        'user__first_name',
        'user__last_name',
        'user__email',
    )
    date_hierarchy = 'date'
    ordering = ('-date',)
    fieldsets = [
        (_("Header"), {
            'fields': [
                ('user', 'event', 'method'),
                'date',
            ],
        }),
        (_("Content"), {
            'fields': [
                'subject',
                ('summary', 'attachment'),
                'note',
                'result',
            ],
        }
        ),
        (_("Sending"), {
            'fields': [('created_by', 'handled_by', 'send', 'dispatched')],
        }
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.handled_by = request.user
        obj.save()

    def get_queryset(self, request):
        # Filter out mass communications which are already dispatched
        # There is no use in displaying the many repetitive rows that
        # arrise from mass communications once they are dispatched. If
        # however not dispatched yet, these communications
        # still require admin action and should be visible.
        qs = super(InteractionAdmin, self).get_queryset(request)
        return qs.exclude(type='mass', dispatched=True)


class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'subject', 'condition', 'only_once', 'dispatch_auto')
    ordering = ('name',)
    readonly_fields = ('sent_to_users_count',)
    exclude = ('sent_to_users',)

    def sent_to_users_count(self, obj):
        return obj.sent_to_users.count()

    def save_form(self, request, form, change):
        super(AutomaticCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        if "_continue" in request.POST and request.POST["_continue"] == "test_mail":
            mailing.send_fake_communication(obj, request.user, request)
        return obj


class MassCommunicationForm(forms.ModelForm):
    class Meta:
        model = MassCommunication
        fields = '__all__'

    def clean_send_to_users(self):
        v = EmailValidator()
        for user in self.cleaned_data['send_to_users']:
            email = user.email
            if email:
                try:
                    v.__call__(email)
                except ValidationError as e:
                    raise ValidationError(
                        _("Invalid email '%(email)s' of user %(user)s: %(exception)s") % {
                            'email': email,
                            'user': user,
                            'exception': e,
                        },
                    )
        return self.cleaned_data['send_to_users']


class MassCommunicationAdmin(large_initial.LargeInitialMixin, admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'date', 'method', 'subject')
    ordering = ('-date',)

    filter_horizontal = ('send_to_users',)

    form = MassCommunicationForm

    formfield_overrides = {
        CharField: {'widget': forms.TextInput(attrs={'size': '60'})},
    }

    """
    fieldsets = [
        (_("Basic"), {
            'fields': [('name', 'method', 'date', 'note',)],
        }),
        (_("Content"), {
            'fields': [
                ('subject', 'subject_en'),
                ('template', 'template_en'),
                ('attachment', 'attach_tax_confirmation'),
            ],
        }),
        (_("Sending"), {
            'fields': ['send_to_users'],
        }),
    ]
    """

    def save_form(self, request, form, change):
        super(MassCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        if "_continue" in request.POST and request.POST["_continue"] == "test_mail":
            mailing.send_fake_communication(obj, request.user, request)

        if "_continue" in request.POST and request.POST["_continue"] == "send_mails":
            try:
                mailing.send_mass_communication(obj, request.user, request)
            except Exception as e:
                messages.error(request, _('While sending e-mails the problem occurred: %s') % e)
                raise e
            # Sending was done, so revert the state of the 'send' checkbox back to False
            obj.date = datetime.datetime.now()
            obj.save()
        return obj


class TerminalConditionInline(admin.TabularInline):
    model = TerminalCondition
    readonly_fields = ("variable_description",)
    extra = 0


class TerminalConditionAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('variable', 'operation', 'value', 'condition')


class ConditionAdmin(ImportExportMixin, admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'as_filter', 'on_dashboard', 'operation', 'condition_string')
    filter_horizontal = ('conds',)
    inlines = [TerminalConditionInline, ]
    fieldsets = [
        (_("Description"), {
            'fields': ['name'],
        }),
        (_("Operator"), {
            'fields': ['operation'],
        }),
        (_("Logical conditions operands"), {
            'fields': ['conds'],
        }),
        (_("Usage"), {
            'fields': ['as_filter', 'on_dashboard'],
        }),
    ]

    ordering = ('name',)


def pair_variable_symbols(self, request, queryset):
    for account_statement in queryset:
        for payment in account_statement.payment_set.all():
            account_statement.pair_vs(payment)
            payment.save()
    messages.info(request, _('Variable symbols succesfully paired.'))


pair_variable_symbols.short_description = _("Pair payments with users based on variable symboles")


def parse_statement(self, request, queryset):
    for statement in queryset:
        from .tasks import parse_account_statement
        parse_account_statement.delay(statement.pk)


parse_statement.short_description = _("Reparse account statement")


class AccountStatementsAdmin(unit_admin_mixin_generator('administrative_unit'), nested_admin.NestedModelAdmin):
    list_display = ('type', 'import_date', 'payments_count', 'csv_file', 'administrative_unit', 'date_from', 'date_to')
    list_filter = ('type',)
    inlines = [PaymentsInlineNoExtra]
    readonly_fields = ('import_date', 'payments_count')
    fields = copy.copy(list_display)
    actions = (
        pair_variable_symbols,
        parse_statement,
    )

    def payments_count(self, obj):
        return obj.payment_set.count()

    # TODO: add reporting of skipped payments to Celery task
    # def save_model(self, request, obj, form, change):
    #     if getattr(obj, 'skipped_payments', None):
    #         skipped_payments_string = ', '.join(["%s %s (%s)" % (p['name'], p['surname'], p['email']) for p in obj.skipped_payments])
    #         messages.info(request, 'Skipped payments: %s' % skipped_payments_string)
    #     payments_without_user = ', '.join(["%s (%s)" % (p.account_name, p.user_identification) for p in obj.payments if not p.user])
    #     if payments_without_user:
    #         messages.info(request, 'Payments without user: %s' % payments_without_user)
    #     obj.save()


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


class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sort',
    )
    save_as = True


class EventAdmin(unit_admin_mixin_generator('administrative_units'), admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'darujme_name',
        'darujme_api_id',
        'darujme_project_id',
        'created',
        'terminated',
        'number_of_members',
        'number_of_recruiters',
        'acquisition_campaign',
        'yield_total',
        'total_expenses',
        'expected_monthly_income',
        'return_of_investmensts',
        'average_yield',
        'average_expense',
    )
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
    list_filter = ('acquisition_campaign', filters.ActiveCampaignFilter)
    search_fields = ('name', )
    inlines = (ExpenseInline,)
    actions = (download_darujme_statement,)
    save_as = True


class RecruiterAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('recruiter_id', 'person_name', 'email', 'telephone', 'problem', 'rating')
    list_filter = ('problem', 'campaigns')
    filter_horizontal = ('campaigns',)


class SourceAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'direct_dialogue')


class TaxConfirmationAdmin(unit_admin_mixin_generator('user_profile__administrative_units'), ImportExportMixin, admin.ModelAdmin):
    change_list_template = "admin/aklub/taxconfirmation/change_list.html"
    list_display = ('user_profile', 'year', 'amount', 'get_pdf', )
    ordering = ('user_profile__last_name', 'user_profile__first_name',)
    list_filter = ['year']
    search_fields = ('user_profile__last_name', 'user_profile__first_name', 'user_profile__userincampaign__variable_symbol',)
    raw_id_fields = ('user_profile',)
    actions = (make_pdfsandwich,)
    list_max_show_all = 10000

    readonly_fields = ['get_pdf', ]
    fields = ['user_profile', 'year', 'amount', 'get_pdf', ]

    def generate(self, request):
        tasks.generate_tax_confirmations.apply_async()
        return HttpResponseRedirect(reverse('admin:aklub_taxconfirmation_changelist'))

    def get_urls(self):
        from django.conf.urls import url
        urls = super(TaxConfirmationAdmin, self).get_urls()
        my_urls = [
            url(
                r'generate',
                self.admin_site.admin_view(self.generate),
                name='aklub_taxconfirmation_generate',
            ),
        ]
        return my_urls + urls


class TaxConfirmationPdfAdmin(PdfSandwichAdmin):
    pass


class TaxConfirmationFieldAdmin(PdfSandwichFieldAdmin):
    pass


@admin.register(AdministrativeUnit)
class AdministrativeUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'ico')
    readonly_fields = ('ico',)


admin.site.register(DonorPaymentChannel, DonorPaymethChannelAdmin)
admin.site.register(UserYearPayments, UserYearPaymentsAdmin)
admin.site.register(NewUser, NewUserAdmin)
admin.site.register(Interaction, InteractionAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(MassCommunication, MassCommunicationAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(TerminalCondition, TerminalConditionAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Recruiter, RecruiterAdmin)
admin.site.register(TaxConfirmation, TaxConfirmationAdmin)
admin.site.register(TaxConfirmationPdf, TaxConfirmationPdfAdmin)
admin.site.register(TaxConfirmationField, TaxConfirmationFieldAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
# register all adminactions
actions.add_to_site(site)
