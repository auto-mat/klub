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
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import CharField, Count, Max, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.html import format_html, format_html_join, mark_safe
from django.utils.translation import ugettext as _

try:
    from django.urls import reverse
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse

from flexible_filter_conditions.admin_filters import UserConditionFilter, UserConditionFilter1

from import_export import fields
from import_export.admin import ImportExportMixin
from import_export.instance_loaders import BaseInstanceLoader
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from import_export_celery.admin_actions import create_export_job_action

from interactions.admin import InteractionInline
from interactions.models import Interaction, InteractionType

from isnull_filter import isnull_filter

import large_initial

import nested_admin

from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from related_admin import RelatedFieldAdmin

from smmapdfs.actions import make_pdfsandwich


from . import darujme, filters, mailing, tasks
from .filters import unit_admin_mixin_generator
from .forms import (
    CompanyProfileAddForm, CompanyProfileChangeForm, UnitUserProfileAddForm,
    UnitUserProfileChangeForm, UserCreateForm, UserUpdateForm,
)
from .models import (
    AccountStatements, AdministrativeUnit, ApiAccount, AutomaticCommunication, BankAccount,
    CompanyProfile, DonorPaymentChannel, Event, Expense,
    MassCommunication, MoneyAccount, NewUser, Payment, Preference, Profile, ProfileEmail, Recruiter,
    Source, TaxConfirmation, Telephone, UserBankAccount,
    UserProfile, UserYearPayments,
)
from .profile_model_resources import (
    ProfileModelResource, get_polymorphic_parent_child_fields,
)
from .profile_model_resources_mixin import ProfileModelResourceMixin


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


class DonorPaymentChannelInlineForm(forms.ModelForm):
    user_bank_account_char = forms.CharField(
        label='user_bank_account',
        max_length=50,
        required=False,
        )

    class Meta():
        model = DonorPaymentChannel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_bank_account_char'].initial = self.instance.user_bank_account

    def save(self, commit=False):
        donor = super().save()
        bank_acc, _ = UserBankAccount.objects.get_or_create(bank_account_number=self.cleaned_data['user_bank_account_char'])
        donor.user_bank_account = bank_acc
        donor.save()
        return super().save()


class DonorPaymentChannelInline(admin.StackedInline):
    model = DonorPaymentChannel
    form = DonorPaymentChannelInlineForm
    extra = 0
    can_delete = True
    show_change_link = True
    readonly_fields = (
        'get_sum_amount',
        'get_payment_count',
        'get_last_payment_date',
        'get_payment_details',
        'get_payment_list_link',
    )
    fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                ('money_account', 'user_bank_account_char'),
                ('regular_payments'),
                ('event'),
                (
                    'get_sum_amount',
                    'get_payment_count',
                    'get_last_payment_date',
                    'get_payment_details',
                    'get_payment_list_link',
                ),
            ),
        }),
        (_('Details'), {
            'classes': ('collapse',),
            'fields': [
                ('VS', 'SS'),
                ('registered_support', 'regular_amount', 'regular_frequency'),
                ('expected_date_of_first_payment', 'exceptional_membership'),
                ('other_support'),
            ],
        }
         )
    )

    def get_payment_list_link(self, obj):
        url = reverse('admin:aklub_payment_changelist')
        if obj.pk:
            redirect_button = mark_safe(
                f"<a href='{url}?user_donor_payment_channel={obj.pk}'><input type='button' value='All payments'></a>"
            )
        else:
            redirect_button = None
        return redirect_button
    get_payment_list_link.short_description = _('All payments')

    def get_sum_amount(self, obj):
        return obj.sum_amount
    get_sum_amount.short_description = _('Total amount')

    def get_payment_count(self, obj):
        return obj.payment_count
    get_payment_count.short_description = _('Total payment count')

    def get_last_payment_date(self, obj):
        return obj.last_payment_date
    get_last_payment_date.short_description = _('Last payment date')

    def get_payment_details(self, obj):
        url = reverse('admin:aklub_donorpaymentchannel_change', args=(obj.pk,))
        if obj.pk:
            redirect_button = mark_safe(
                                f"<a href='{url}'><input type='button' value='Details'></a>"
                                )
        else:
            redirect_button = None
        return redirect_button
    get_payment_details.short_description = _('Payment Details')

    def get_queryset(self, request):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            queryset = DonorPaymentChannel.objects.filter(money_account__administrative_unit__in=request.user.administrated_units.all())
        else:
            queryset = super().get_queryset(request)
        return queryset.\
            annotate(sum_amount=Sum('payment__amount')).\
            annotate(payment_count=Count('payment')).\
            annotate(last_payment_date=Max('payment__date'))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "money_account":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = MoneyAccount.objects.filter(administrative_unit__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = MoneyAccount.objects.all()

        if db_field.name == "event":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Event.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Event.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
        'operation_id'
    )
    extra = 0

    def user__campaign(self, obj):
        return obj.user.campaign


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


def send_mass_communication_action(self, request, queryset):
    """Mass communication action

    Determine the list of user ids from the associated
    queryset and redirect us to insert form for mass communications
    with the send_to_users M2M field prefilled with these
    users."""
    if queryset.model == Profile:
        queryset = Profile.objects.filter(id__in=queryset)
    elif queryset.model == DonorPaymentChannel:
        queryset = Profile.objects.filter(userchannels__in=queryset)
    redirect_url = large_initial.build_redirect_url(
        request,
        "admin:aklub_masscommunication_add",
        params={'send_to_users': queryset},
    )

    return HttpResponseRedirect(redirect_url)


send_mass_communication_action.short_description = _("Send mass communication")


def get_profile_admin_export_base_order_fields():
    return [
        'administrative_units',
        'email',
        'telephone',
        'donor',
        'username',
        'date_joined',
        'addressment',
        'addressment_on_envelope',
        'language',
        'street',
        'city',
        'country',
        'zip_code',
        'different_correspondence_address',
        'correspondence_street',
        'correspondence_city',
        'correspondence_country',
        'correspondence_zip_code',
        'other_support',
        'public',
        'note',
        'send_mailing_lists',
        'newsletter_on',
        'call_on',
        'challenge_on',
        'letter_on',
    ]


def get_profile_admin_model_import_export_exclude_fields():
    return [
        'id',
        'is_superuser',
        'is_staff',
        'administrated_units',
        'polymorphic_ctype',
        'profile_ptr',
        'last_login',
        'groups',
        'user_permissions',
        'is_active',
        'password',
        'campaigns',
        'profile_text',
        'profile_picture',
        'club_card_available',
        'club_card_dispatched',
        'other_benefits',
        'created',
        'updated',
    ]


class UserProfileLoaderClass(BaseInstanceLoader):
    def get_instance(self, row):
        obj = None
        if row.get('email'):
            try:
                obj = ProfileEmail.objects.get(email=row['email']).user
            except ProfileEmail.DoesNotExist:
                pass
        return obj


class UserProfileResource(ProfileModelResourceMixin):
    class Meta:
        model = UserProfile
        exclude = get_profile_admin_model_import_export_exclude_fields()
        import_id_fields = ('email', )
        export_order = (
            get_profile_admin_export_base_order_fields() +
            [
                'title_before', 'first_name', 'last_name',
                'title_after', 'sex', 'age_group', 'birth_month',
                'birth_day',
            ]
        )
        instance_loader_class = UserProfileLoaderClass
        clean_model_instances = True


class CompanyProfileLoaderClass(BaseInstanceLoader):
    def get_instance(self, row):
        obj = None
        if row.get('crn'):
            try:
                obj = CompanyProfile.objects.get(crn=row['crn'])
            except CompanyProfile.DoesNotExist:
                pass
        if row.get('tin'):
            try:
                obj = CompanyProfile.objects.get(crn=row['tin'])
            except CompanyProfile.DoesNotExist:
                pass
        return obj


class CompanyProfileResource(ProfileModelResourceMixin):
    class Meta:
        model = CompanyProfile
        exclude = get_profile_admin_model_import_export_exclude_fields()
        import_id_fields = ('crn',)
        export_order = (
            get_profile_admin_export_base_order_fields() +
            [
                'name', 'crn', 'tin',
                'contact_first_name', 'contact_last_name',
            ]
        )
        instance_loader_class = CompanyProfileLoaderClass
        clean_model_instances = True

    def dehydrate_email(self, profile):
        emails = ProfileEmail.objects.filter(user=profile)
        return ',\n'.join(email.email for email in emails)

    def export_dehydrate_email(self, profile):
        try:
            email = ProfileEmail.objects.get(user=profile, is_primary=True)
        except ProfileEmail.DoesNotExist:
            email = ProfileEmail.objects.filter(user=profile).first()
        if email:
            return email.email
        return None

    def export_field(self, field, obj):
        field_name = self.get_field_name(field)
        method = getattr(self, 'dehydrate_%s' % field_name, None)
        if method is not None:
            if method.__name__ == 'dehydrate_email':
                return self.export_dehydrate_email(obj)
            else:
                return method(obj)
        return field.export(obj)


class ProfileResource(ProfileModelResource):
    class Meta:
        model = Profile
        exclude = get_profile_admin_model_import_export_exclude_fields()
        import_id_fields = ('email', )
        export_order = (
            get_profile_admin_export_base_order_fields() +
            [
                'name', 'crn', 'tin', 'sex', 'title_after',
                'first_name', 'last_name', 'title_before',
                'birth_month', 'birth_day', 'profile_type',
            ]
        )
        clean_model_instances = True

    profile_type = fields.Field()

    def before_import_row(self, row, **kwargs):
        row['is_superuser'] = 0
        row['is_staff'] = 0
        row['email'] = row['email'].lower() if row.get('email') else ''
        row['polymorphic_ctype_id'] = ContentType.objects.get(model=row['profile_type']).id
        self._get_row_model_column(row=row)

    def import_field(self, field, obj, data, is_m2m=False):
        if field.attribute and field.column_name in data:  # and not getattr(obj, field.column_name):
            field.save(obj, data, is_m2m)

    def dehydrate_profile_type(self, profile):
        if profile.pk:
            polymorphic_ctype = profile.polymorphic_ctype
            model = polymorphic_ctype.model_class()
            return model._meta.model_name
        else:
            return None

    def _get_row_model_column(self, row):
        all_child_models_fields = get_polymorphic_parent_child_fields(self._meta.model)
        for model_name, model_fields in all_child_models_fields.items():
            for field in model_fields:
                if not row.get(field) and field in row:
                    del row[field]
        return row

    def _set_child_model_field_value(self, obj, data):
        all_child_models_fields = get_polymorphic_parent_child_fields(self._meta.model)
        for model_name, model_fields in all_child_models_fields.items():
            for field in model_fields:
                if hasattr(obj, field):
                    if data.get(field):
                        setattr(obj, field, data[field])

    def __get_row_data(self, row):
        return (row.split(':')[0].strip(), row.split(':')[-1].strip())


class ProfileMergeForm(merge.MergeForm):
    def __init__(self, *args, **kwargs):
        ret_val = super().__init__(*args, **kwargs)
        self.fields['sex'].required = False
        return ret_val

    class Meta:
        model = Profile
        fields = '__all__'


class PreferenceInline(admin.StackedInline):
    model = Preference
    extra = 0
    max_number = 1
    can_delete = False
    fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                ('public', 'send_mailing_lists'),
                ('newsletter_on', 'call_on'),
                ('challenge_on', 'letter_on'),
            ),
        }),
    )

    def get_queryset(self, request):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            return Preference.objects.filter(administrative_unit__in=request.user.administrated_units.all())
        else:
            return super().get_queryset(request)


class TelephoneInline(admin.TabularInline):
    model = Telephone
    extra = 0
    can_delete = True
    show_change_link = True


class ProfileEmailAdminForm(forms.ModelForm):
    class Meta:
        model = ProfileEmail
        fields = '__all__'

    def check_duplicate(self, *args, **kwargs):
        cleaned_data = kwargs['cleaned_data']
        qs = ProfileEmail.objects.filter(
            email=cleaned_data['email'],
            user=cleaned_data['user'],
        )
        msg = _('Duplicate email address for this user')
        if cleaned_data.get('email'):
            cleaned_data['email'] = cleaned_data['email'].lower()
        if not cleaned_data.get('id'):
            if qs.filter(email=cleaned_data['email'], user=cleaned_data['user']).exists():
                self.add_error('email', msg)
                return True
        else:
            if 'email' in self.changed_data:
                if qs.filter(email=cleaned_data['email'], user=cleaned_data['user']).exists():
                    self.add_error('email', msg)
                    return True

    def check_unique(self, *args, **kwargs):
        cleaned_data = kwargs['cleaned_data']
        model = cleaned_data['user']._meta.model_name
        qs = ProfileEmail.objects.filter(
            user__polymorphic_ctype=ContentType.objects.get(model=model),
        )
        msg = _('Email address exist')
        if cleaned_data.get('email'):
            cleaned_data['email'] = cleaned_data['email'].lower()
        if not cleaned_data.get('id'):
            if qs.filter(email=cleaned_data['email']).exists():
                self.add_error('email', msg)
                return True
        else:
            if (qs.filter(email=cleaned_data['email']).exclude(user=cleaned_data['user']).exists()):
                self.add_error('email', msg)
                return True

    def clean(self):
        cleaned_data = super().clean()
        if self.check_duplicate(cleaned_data=cleaned_data):
            return cleaned_data
        if self.check_unique(cleaned_data=cleaned_data):
            return cleaned_data


class ProfileEmailInline(admin.TabularInline):
    model = ProfileEmail
    extra = 0
    can_delete = True
    show_change_link = True
    form = ProfileEmailAdminForm


class RedirectMixin(object):
    def response_add(self, request, obj, post_url_continue=None):
        response = super(PolymorphicChildModelAdmin, self).response_add(
            request, obj, post_url_continue,)
        if not hasattr(response, 'url'):
            return response
        elif 'add' in response.url or 'change' in response.url:
            return response
        else:
            return redirect('admin:aklub_' + self.redirect_page + '_changelist')

    def response_change(self, request, obj):
        response = super(PolymorphicChildModelAdmin, self).response_change(
            request, obj,)
        if not hasattr(response, 'url'):
            return response
        elif 'change' in response.url:
            return response
        return redirect('admin:aklub_' + self.redirect_page + '_changelist')


def child_redirect_mixin(redirect):
    class RedMixin(RedirectMixin):
        redirect_page = redirect
    return RedMixin


class MoneyAccountChildAdmin(
                    unit_admin_mixin_generator('administrative_unit'),
                    PolymorphicChildModelAdmin,
                    ):
    """ Base admin class for all child models """
    base_model = MoneyAccount


@admin.register(ApiAccount)
class ApiAccountAdmin(
                child_redirect_mixin('apiaccount'),
                unit_admin_mixin_generator('administrative_unit'),
                MoneyAccountChildAdmin,
                ):
    """ Api account polymorphic admin model child class """
    base_model = ApiAccount
    show_in_index = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = Event.objects.filter(administrative_units__in=request.user.administrated_units.all())
            else:
                kwargs["queryset"] = Event.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(BankAccount)
class BankAccountAdmin(
                child_redirect_mixin('bankaccount'),
                unit_admin_mixin_generator('administrative_unit'),
                MoneyAccountChildAdmin,
                ):
    """ bank account polymorphic admin model child class """
    base_model = BankAccount
    show_in_index = True


@admin.register(MoneyAccount)
class MoneyAccountParentAdmin(PolymorphicParentModelAdmin):
    """ The parent model admin """
    base_model = MoneyAccount
    child_models = (ApiAccount, BankAccount)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class UserBankAccountAdmin(admin.ModelAdmin):
    model = UserBankAccount

    search_fields = (
        'bank_account', 'bank_account_number',
    )

    list_filter = (
        'bank_account', 'bank_account_number',
    )


class ProfileAdminMixin:
    """ ProfileAdmin mixin """

    def date_format(self, obj):
        return list(map(lambda o: o.strftime('%d. %m. %Y'), obj))

    def get_donor_details(self, obj, attr, *args):
        channels = obj.userchannels.all()
        results = []
        for channel in channels:
            if channel.regular_payments == 'regular':
                if self.request.user.has_perm('aklub.can_edit_all_units') or \
                        (channel.bank_account and channel.bank_account.administrative_unit in self.request.user.administrated_units.all()):
                    results.append(getattr(channel, attr, '-') or '-')
        return results

    def get_donor(self, obj):
        if not self.request.user.has_perm('aklub.can_edit_all_units'):
            result = obj.userchannels.filter(
                            bank_account__administrative_unit__in=self.request.user.administrated_units.all(),
                            regular_payments='regular',
            )
        else:
            result = obj.userchannels.filter(regular_payments='regular')
        return result

    def registered_support_date(self, obj):
        result = self.get_donor_details(obj, "registered_support")
        return ',\n'.join(d.strftime('%Y-%m-%d') for d in result)

    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'userchannels__registered_support'

    def regular_amount(self, obj):
        result = self.get_donor_details(obj, "regular_amount")
        return ',\n'.join(str(d) for d in result)

    regular_amount.short_description = _("Regular amount")
    regular_amount.admin_order_field = 'userchannels__regular_amount'

    def donor_delay(self, obj):
        donors = self.get_donor(obj)
        result = []
        for d in donors:
            if isinstance(d.regular_payments_delay(), (bool,)):
                result.append('ok')
            else:
                result.append(str(d.regular_payments_delay().days) + ' days')
        return ',\n'.join(result)

    donor_delay.short_description = _("Payment delay")
    donor_delay.admin_order_field = 'donor_delay'

    def donor_extra_money(self, obj):
        result = self.get_donor_details(obj, "extra_money")
        return ',\n'.join(str(d) for d in result)

    donor_extra_money.short_description = _("Extra money")
    donor_extra_money.admin_order_field = 'donor_extra_money'

    def donor_frequency(self, obj):
        result = self.get_donor_details(obj, "regular_frequency")
        return ',\n'.join(str(d) for d in result)

    donor_frequency.short_description = _("Donor frequency")
    donor_frequency.admin_order_field = 'donor_frequency'

    def total_payment(self, obj):
        if self.request.user.has_perm('aklub.can_edit_all_units'):
            administrative_units = obj.administrative_units.all()
        else:
            administrative_units = self.request.user.administrated_units.all()

        results = []
        for unit in administrative_units:
            result = Payment.objects.filter(
                        user_donor_payment_channel__user=obj,
                        user_donor_payment_channel__money_account__administrative_unit=unit,
                        ).aggregate(Count('amount'), Sum('amount'))
            results.append(f"{unit}: {result['amount__sum']} Kč ({result['amount__count']})")
        return ',\n'.join(results)

    total_payment.short_description = _("Total payment")
    total_payment.admin_order_field = 'Total payment'

    def email_anchor(self, obj):
        return ''

    email_anchor.short_description = _(mark_safe('<a href="#profileemail_set-group">Details</a>'))

    def get_sum_amount(self, obj):
        return obj.sum_amount
    get_sum_amount.admin_order_field = 'sum_amount'
    get_sum_amount.short_description = _("Sum of all payments")

    def get_payment_count(self, obj):
        return obj.payment_count
    get_payment_count.admin_order_field = 'payment_count'
    get_payment_count.short_description = _("Payments count")

    def get_last_payment_date(self, obj):
        return obj.last_payment_date
    get_last_payment_date.admin_order_field = 'last_payment_date'
    get_last_payment_date.short_description = _("Date of last payment")

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).prefetch_related(
            'telephone_set',
            'profileemail_set',
            'administrative_units',
            'userchannels',
            'userchannels__event',
        ).annotate(
            sum_amount=Sum('userchannels__payment__amount'),
            payment_count=Count('userchannels__payment'),
            last_payment_date=Max('userchannels__payment__date'),
        )


class ProfileAdmin(
    filters.AdministrativeUnitAdminMixin,
    ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin,
    ProfileAdminMixin,
    UserAdmin, PolymorphicParentModelAdmin,
):
    polymorphic_list = True
    resource_class = ProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    # merge_form = UserMergeForm
    # add_form = UserCreateForm
    # form = UserUpdateForm
    base_model = Profile
    child_models = (UserProfile, CompanyProfile)

    list_display = (
        'person_name',
        'get_email',
        'get_administrative_units',
        'addressment',
        'get_addressment',
        'get_last_name_vokativ',
        'get_main_telephone',
        'title_before',
        'title_after',
        'is_active',
        'sex',
        'crn',
        'tin',
        'is_staff',
        'registered_support_date',
        'get_event',
        'regular_amount',
        'date_joined',
        'last_login',
    )

    advanced_filter_fields = (
        'email',
        'addressment',
        'telephone__telephone',
        'userprofile__title_before',
        'userprofile__first_name',
        'userprofile__last_name',
        'userprofile__title_after',
        'userprofile__sex',
        'companyprofile__crn',
        'companyprofile__tin',
        'companyprofile__name',
        'is_staff',
        'date_joined',
        'last_login',
        ('userchannels__event__name', _("Jméno kampaně")),
    )
    list_editable = (
        'addressment',
    )
    search_fields = (
        'email',
        'userprofile__title_before',
        'userprofile__first_name',
        'userprofile__last_name',
        'userprofile__title_after',
        'companyprofile__name',
        'telephone__telephone',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'language',
        'userchannels__event',
        filters.RegularPaymentsFilter,
        filters.EmailFilter,
        filters.TelephoneFilter,
        filters.NameFilter,
    )

    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    def event(self, obj):
        result = Profile.objects.get(id=obj.id)
        donors = result.userchannels.select_related().all()
        return [e.event for e in donors]

    event.short_description = _("Event")
    event.admin_order_field = 'event'

    def sex(self, obj):
        return self.sex if hasattr(obj, 'sex') else None

    sex.short_description = _("Gender")
    sex.admin_order_field = 'userprofile__sex'

    def crn(self, obj):
        return self.crn if hasattr(obj, 'crn') else None

    crn.short_description = _("Company Registration Number")
    crn.admin_order_field = 'companyprofile__crn'

    def tin(self, obj):
        return self.tin if hasattr(obj, 'tin') else None

    tin.short_description = _("Tax Identification Number")
    tin.admin_order_field = 'companyprofile__tin'

    def title_before(self, obj):
        return self.title_before if hasattr(obj, 'title_before') else None

    title_before.short_description = _("Title before")
    title_before.admin_order_field = 'userprofile__title_before'

    def title_after(self, obj):
        return self.title_after if hasattr(obj, 'title_after') else None

    title_after.short_description = _("Title after")
    title_after.admin_order_field = 'userprofile__title_after'

    def delete_queryset(self, request, queryset):
        """
        Fix 'IntegrityError update or delete on table
        "aklub_profile" violates foreign key constraint' error,
        delete mixed models ('User/CompanyProfile' model) in the
        'Profile' admin model list view, via
        'Delete selected Profiles' action
        """
        # Filter queryset according 'Profile' child models type
        user_profile_qs = queryset.instance_of(UserProfile)
        company_profile_qs = queryset.instance_of(CompanyProfile)
        # Delete standalone queryset
        if user_profile_qs:
            super().delete_queryset(request, user_profile_qs)
        if company_profile_qs:
            super().delete_queryset(request, company_profile_qs)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class DonorPaymentChannelLoaderClass(BaseInstanceLoader):
    def get_instance(self, row):
        user = ProfileEmail.objects.get(email=row['email']).user
        try:
            event = Event.objects.get(name=row.get('event'))
            money_account = BankAccount.objects.get(bank_account_number=row.get('money_account'))
            obj = DonorPaymentChannel.objects.get(
                                            user=user,
                                            event=event,
                                            money_account=money_account,
            )
        except Event.DoesNotExist:
            raise ValidationError({'event': 'Event with this name doesnt exist'})
        except MoneyAccount.DoesNotExist:
            raise ValidationError({'moneyaccount': 'MoneyAccount with this bank_number doesnt exist'})

        except DonorPaymentChannel.DoesNotExist:
            return None

        return obj


class DonorPaymentChannelResource(ModelResource):
    email = fields.Field()
    user_bank_account = fields.Field()
    event = fields.Field(
                    column_name='event',
                    attribute='event',
                    widget=ForeignKeyWidget(Event, 'name'),
    )

    money_account = fields.Field(
                    column_name='money_account',
                    attribute='money_account',
                    widget=ForeignKeyWidget(MoneyAccount, 'bankaccount__bank_account_number'),
    )

    class Meta:
        model = DonorPaymentChannel
        fields = (
                'email', 'user', 'money_account', 'event', 'VS', 'SS', 'regular_frequency', 'expected_date_of_first_payment',
                'regular_amount', 'regular_payments', 'user_bank_account', 'end_of_regular_payments',
        )
        import_id_fields = ('email', )
        clean_model_instances = True
        instance_loader_class = DonorPaymentChannelLoaderClass

    def before_import_row(self, row, **kwargs):
        try:
            row['email'] = row['email'].lower()
            row['user'] = ProfileEmail.objects.get(email=row['email']).user.id
        except ProfileEmail.DoesNotExist:
            raise ValidationError({"email": "User with this email doesn't exist"})

    def import_obj(self, obj, data, dry_run):
        super(ModelResource, self).import_obj(obj, data, dry_run)
        if data.get('user_bank_account'):
            user_bank_acc, _ = UserBankAccount.objects.get_or_create(bank_account_number=data.get('user_bank_account'))
            obj.user_bank_account = user_bank_acc
        obj.user = ProfileEmail.objects.get(email=data['email']).user
        return obj

    def dehydrate_user_bank_account(self, donor):
        if donor.user_bank_account:
            obj = donor.user_bank_account.bank_account_number
        else:
            obj = ''
        return obj

    def dehydrate_email(self, donor):
        if hasattr(donor, 'user'):
            try:
                email = ProfileEmail.objects.get(user=donor.user, is_primary=True)
            except ProfileEmail.DoesNotExist:
                email = ProfileEmail.objects.filter(user=donor.user).first()
            return email.email
        return ''

    def dehydrate_user(self, donor):
        if hasattr(donor, 'user'):
            return donor.user.username


# -- ADMIN FORMS --
class DonorPaymethChannelAdmin(
    unit_admin_mixin_generator('user__administrative_units'),
    ImportExportMixin,
    AdminAdvancedFiltersMixin,
    RelatedFieldAdmin,
    nested_admin.NestedModelAdmin,
):
    list_display = (
        'person_name',
        'user__email',
        # 'user__telephone_url',
        # 'source',
        'event',
        'VS',
        'SS',
        'number_of_payments',
        'payment_total',
        'last_payment_amount',
        'regular_amount',
        'payment_delay',
        'last_payment_date',
        'extra_payments',
        'user__is_active',
        # 'registered_support_date',
        # 'regular_payments_info',
        # 'total_contrib_string',
        # 'next_communication_date',
        # 'next_communication_method',
        # 'email_confirmed',
    )
    advanced_filter_fields = (
        'user__userprofile__first_name',
        'user__userprofile__last_name',
        'user__email',
        # 'user__telephone',
        # 'source',
        ('campaign__name', _("Campaign name")),
        'VS',
        'SS',
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
    ]
    search_fields = [
        'user__userprofile__first_name',
        'user__userprofile__last_name',
        'VS',
        'SS',
        'user__email',
        # 'user__telephone',
    ]
    ordering = ('user__userprofile__last_name', 'user__companyprofile__name')
    actions = (
        send_mass_communication_action,
        show_payments_by_year,
    )
    resource_class = DonorPaymentChannelResource
    save_as = True
    list_max_show_all = 10000
    list_per_page = 100
    inlines = (PaymentsInline, )
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
                ('event', 'user', 'money_account',),
                ('user_telephone_url',),
                ('user_note',),
            ],
        }),
        (_('Support'), {
            'fields': [
                'VS',
                'SS',
                'registered_support',
                (
                    'regular_payments', 'regular_frequency',
                    'regular_amount', 'expected_date_of_first_payment',
                    'exceptional_membership'
                ),
                'other_support', 'old_account',
            ],
        }),
    ]

    def user_note(self, obj):
        return obj.user.note

    def user_telephone_url(self, obj):
        return obj.user.telephone_url()


class UserYearPaymentsAdmin(DonorPaymethChannelAdmin):
    list_display = (
        'person_name',
        'user__email',
        # 'source',
        'VS',
        'SS',
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
        ('registered_support', DateRangeFilter), UserConditionFilter, UserConditionFilter1,
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


def add_user_bank_acc_to_dpch(self, request, queryset):
    for payment in queryset:
        if payment.user_donor_payment_channel and payment.account and payment.bank_code:
            user_bank_acc, created = UserBankAccount.objects.get_or_create(
                                        bank_account_number=str(payment.account) + '/' + str(payment.bank_code),
            )
            donor = payment.user_donor_payment_channel
            donor.user_bank_account = user_bank_acc
            donor.save()
    messages.info(request, _('User bank accounts were updated.'))


add_user_bank_acc_to_dpch.short_description = _("add user bank account  to current donor payment channel (rewrite)")


def payment_pair_action(self, request, queryset):
    for payment in queryset:
        if payment.account_statement:
            payment.account_statement.payment_pair(payment)
    messages.info(request, _('Payments succesfully paired with donor payment channels.'))


payment_pair_action.short_description = _("pair payments from account statement with donor payment channels")


def payment_request_pair_action(self, request, queryset):
    if request.user.administrated_units.count() == 1:
        # Create imagine AccountStatement to use payment_pair method with user's administrated_units
        statement = AccountStatements()
        statement.administrative_unit = request.user.administrated_units.first()
        for payment in queryset:
            statement.payment_pair(payment)
        messages.info(request, _('Payments succesfully paired with donor payment channels which are under your administrative unit.'))
    else:
        messages.error(request, _('Your administrated unit have to be set to pair payments.'))


payment_request_pair_action.short_description = _("pair payments without account statement (need to be admin of administrative unit)")


class PaymentAdmin(
    unit_admin_mixin_generator('user_donor_payment_channel__user__administrative_units'),
    ImportExportMixin,
    RelatedFieldAdmin,
):
    actions = (add_user_bank_acc_to_dpch, payment_pair_action, payment_request_pair_action)
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
    list_select_related = (
        'user_donor_payment_channel__user',
        'user_donor_payment_channel__event',
        'account_statement',
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
        'user_donor_payment_channel__user__userprofile__last_name',
        'user_donor_payment_channel__user__userprofile__first_name',
        'user_donor_payment_channel__user__companyprofile__name',
        'amount',
        'BIC',
        'KS',
        'SS',
        'VS',
        'VS2',
        'account',
        'account_name',
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
        'created',
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


class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method_type', 'subject', 'condition', 'only_once', 'dispatch_auto')
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
    list_display = ('name', 'date', 'method_type', 'subject')
    ordering = ('-date',)

    filter_horizontal = ('send_to_users',)
    autocomplete_fields = ('send_to_users',)

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

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "send_to_users":
            kwargs["queryset"] = Profile.objects.filter(is_active=True, preference__send_mailing_lists=True).distinct()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

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


def pair_payment_with_dpch(self, request, queryset):
    for account_statement in queryset:
        for payment in account_statement.payment_set.all():
            account_statement.payment_pair(payment)
            payment.save()
    messages.info(request, _('Payments succesfully paired.'))


pair_payment_with_dpch.short_description = _("Pair payments with users based on variable symboles or user bank account")


def parse_statement(self, request, queryset):
    for statement in queryset:
        from .tasks import parse_account_statement
        parse_account_statement.delay(statement.pk)


parse_statement.short_description = _("Reparse CSV file")


class AccountStatementsAdmin(unit_admin_mixin_generator('administrative_unit'), nested_admin.NestedModelAdmin):
    list_display = ('type', 'import_date', 'payments_count', 'paired_payments', 'csv_file', 'administrative_unit', 'date_from', 'date_to')
    list_filter = ('type',)
    inlines = [PaymentsInlineNoExtra]
    readonly_fields = ('import_date', 'payments_count', 'paired_payments')
    fields = copy.copy(list_display)
    actions = (
        pair_payment_with_dpch,
        parse_statement,
    )

    def payments_count(self, obj):
        return obj.payment_set.count()

    def paired_payments(self, obj):
        return obj.payment_set.filter(user_donor_payment_channel__isnull=False).count()

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


class EventAdmin(unit_admin_mixin_generator('administrative_units'), admin.ModelAdmin):
    list_display = (
        'name',
        'id',
        'slug',
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

    def batch_download(self, request, queryset):
        links = []
        for q in queryset:
            file_field = q.taxconfirmationpdf_set.get().pdf
            if file_field:
                links.append(file_field.url)
        return HttpResponse("\n".join(links), content_type='text/plain')

    batch_download.short_description = _("generate download links for pdf files")

    change_list_template = "admin/aklub/taxconfirmation/change_list.html"
    list_display = ('user_profile', 'get_email', 'year', 'amount', 'get_pdf', 'administrative_unit', 'get_status', 'get_send_time', )
    ordering = (
        'user_profile__userprofile__last_name',
        'user_profile__userprofile__first_name',
        'user_profile__companyprofile__name',
    )
    list_filter = [
        'year',
        'administrative_unit',
        filters.ProfileHasEmail,
        filters.ProfileHasFullAdress,
    ]
    search_fields = (
        'user_profile__userprofile__last_name',
        'user_profile__userprofile__first_name',
        'user_profile__companyprofile__name',
        'user_profile__userchannels__VS',
    )
    raw_id_fields = ('user_profile',)
    actions = (make_pdfsandwich, batch_download)
    list_max_show_all = 10000
    list_select_related = (
        'user_profile__userprofile',
        'user_profile__companyprofile',
    )

    readonly_fields = ['get_pdf', 'get_email', 'get_status', 'get_send_time']
    fields = ['user_profile', 'year', 'amount', 'get_pdf', 'administrative_unit', ]

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

    def get_email(self, obj):
        try:
            email = obj.user_profile.profileemail_set.get(is_primary=True)
        except ProfileEmail.DoesNotExist:
            email = None
        return email

    def get_status(self, obj):
        return obj.taxconfirmationpdf_set.get().status

    def get_send_time(self, obj):
        return obj.taxconfirmationpdf_set.get().sent_time


@admin.register(AdministrativeUnit)
class AdministrativeUnitAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'id',
        'ico',
        'from_email_address',
        'from_email_str',
        'color',
    )


class BaseProfileChildAdmin(PolymorphicChildModelAdmin,):
    """ Base admin class for all Profile child models """
    merge_form = ProfileMergeForm

    def save_formset(self, request, form, formset, change):
        formset.save()
        if issubclass(formset.model, DonorPaymentChannel):
            for f in formset.forms:
                obj = f.instance
                obj.generate_VS()

        if issubclass(formset.model, Interaction):
            for f in formset.forms:
                obj = f.instance
                if not obj.created_by:
                    obj.created_by = request.user
                obj.handled_by = request.user

        return super().save_formset(request, form, formset, change)

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            inline.form.request = request
            yield inline.get_formset(request, obj), inline

    readonly_fields = (
        'userattendance_links', 'date_joined', 'last_login', 'get_main_telephone',
        'get_email', 'regular_amount', 'donor_delay', 'registered_support_date',
        'donor_frequency', 'total_payment', 'donor_extra_money', 'email_anchor',
    )

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        if not obj:
            inlines = []
        return inlines

    inlines = [
        PreferenceInline, ProfileEmailInline, TelephoneInline,
        DonorPaymentChannelInline, InteractionInline,
    ]


@admin.register(UserProfile)
class UserProfileAdmin(
        child_redirect_mixin('userprofile'), filters.AdministrativeUnitAdminMixin,
        ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin, ProfileAdminMixin,
        BaseProfileChildAdmin,
):
    """ User profile polymorphic admin model child class """
    base_model = UserProfile
    show_in_index = True
    resource_class = UserProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    change_form_template = "admin/aklub/userprofile_changeform.html"
    list_display = (
        'person_name',
        'username',
        'get_email',
        'get_main_telephone',
        'get_administrative_units',
        'get_event',
        'date_joined',
        'get_sum_amount',
        'get_payment_count',
        'get_last_payment_date',
        'regular_amount',
        'donor_delay',
        'donor_extra_money',
    )

    actions = (
        create_export_job_action,
        send_mass_communication_action,
    )
    advanced_filter_fields = (
        'profileemail__email',
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
        ('userchannels__event__name', _("Jméno kampaně")),
    )
    search_fields = (
        'email',
        'username',
        'title_before',
        'first_name',
        'last_name',
        'title_after',
        'telephone__telephone',
        'profileemail__email',
    )
    list_filter = (
        'administrative_units',
        'userchannels__registered_support',
        'preference__send_mailing_lists',
        isnull_filter('userchannels__payment', _('Has any payment'), negate=True),
        'userchannels__extra_money',
        'userchannels__regular_amount',
        'userchannels__regular_frequency',
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'language',
        'userchannels__event',
        filters.RegularPaymentsFilter,
        filters.EmailFilter,
        filters.TelephoneFilter,
        filters.NameFilter,
        UserConditionFilter, UserConditionFilter1,
    )
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    add_fieldsets = (
        (_('Personal data'), {
            'classes': ('wide',),
            'fields': (
                'username', ('first_name', 'last_name'), 'sex',
                'email', 'telephone', 'is_active',
                ('birth_day', 'birth_month', 'age_group'),
                'administrative_units',
                'hidden_lock_change'
            ),
        }),
    )
    edit_fieldsets = (
        (_('Personal data'), {
            'classes': ('wide',),
            'fields': (
                'username', ('first_name', 'last_name'), ('title_before', 'title_after'), 'sex',
                'is_active',
                ('birth_day', 'birth_month', 'age_group'),
                ('get_email', 'email_anchor'),
                'get_main_telephone',
                'note',
                'administrative_units',
                'total_payment',
                ('registered_support_date', 'regular_amount', 'donor_frequency', 'donor_delay', 'donor_extra_money'),
            ),
        }),
        (_('Contact data'), {
            'classes': ('wide', ),
            'fields': [
                ('street', 'city',),
                ('country', 'zip_code'),
                ('addressment', 'addressment_on_envelope'),
                'different_correspondence_address',
            ],
        }
         ),
        (_('Correspondence address'), {
            'classes': ('collapse', ),
            'fields': [
                ('correspondence_street', 'correspondence_city',),
                ('correspondence_country', 'correspondence_zip_code'),
            ],
        }
         ),
    )
    superuser_fieldsets = (
        (_('Rights and permissions'), {
            'classes': ('collapse',),
            'fields': [
                ('password',),
                ('is_staff', 'is_superuser', 'is_active'),
                'groups',
                'administrated_units',
            ],
        }
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            if obj:
                self.form = UserUpdateForm
            else:
                self.form = UserCreateForm
        else:
            if obj:
                self.form = UnitUserProfileChangeForm
            else:
                self.form = UnitUserProfileAddForm

        form = super().get_form(request, obj, **kwargs)
        form.base_fields['language'].required = False
        form.request = request
        return form

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

    def add_view(self, request, form_url='', extra_context=None):
        """ email duplicity handler """
        data = request.POST
        if data.get('email') and data.get('administrative_units'):
            try:
                email = ProfileEmail.objects.get(email=data.get('email'))
                unit = AdministrativeUnit.objects.get(id=data.get('administrative_units'))
                user = email.user
                user.administrative_units.add(unit)
                user.save()
                messages.warning(request, 'User With this email is in database already. You can edit him now')
                url = reverse('admin:aklub_userprofile_change', args=(user.pk,))
                return HttpResponseRedirect(url)

            except ProfileEmail.DoesNotExist:
                pass

        return super().add_view(request)

    def change_view(self, request, object_id, extra_context=None, **kwargs):
        from helpdesk.query import query_to_base64
        extra_context = extra_context or {}
        extra_context['urlsafe_query'] = query_to_base64({
            'search_string': "OR".join([pe.email for pe in ProfileEmail.objects.filter(user__pk=object_id)]),
            'search_profile_pks': [object_id],
        })
        extra_context['display_fields'] = serializers.serialize('json', InteractionType.objects.all())

        ignore_required = ['id', 'user', 'baseinteraction2_ptr']
        extra_context['required_fields'] = [
                    field.name for field in Interaction._meta.get_fields()
                    if not field.blank and field.name not in ignore_required
        ]
        extra_context['object_id'] = object_id
        return super().change_view(
            request,
            object_id,
            extra_context=extra_context,
            **kwargs,
        )


@admin.register(CompanyProfile)
class CompanyProfileAdmin(
        child_redirect_mixin('companyprofile'), filters.AdministrativeUnitAdminMixin,
        ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin,
        BaseProfileChildAdmin, ProfileAdminMixin,
):
    """ Company profile polymorphic admin model child class """
    base_model = CompanyProfile
    show_in_index = True
    resource_class = CompanyProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    list_display = (
        'name',
        'crn',
        'tin',
        'email',
        'get_main_telephone',
        'get_event',
        'variable_symbol',
        'regular_amount',
        'is_staff',
        'date_joined',
        'last_login',
        'contact_first_name',
        'contact_last_name',
    )
    advanced_filter_fields = (
        'email',
        'telephone__telephone',
        'name',
        'crn',
        'tin',
        'is_staff',
        'date_joined',
        'last_login',
        ('userchannels__event__name', _("Jméno kampaně")),
    )
    search_fields = (
        'email',
        'name',
        'telephone__telephone',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'language',
        'userchannels__event',
        filters.RegularPaymentsFilter,
        filters.EmailFilter,
        filters.TelephoneFilter,
        filters.NameFilter,
    )

    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    add_fieldsets = (
        (_('Personal data'), {
            'classes': ('wide',),
            'fields': (
                'username', ('name'),
                'is_active',
                ('contact_first_name', 'contact_last_name',),
                'no_crn_check',
                'email',
                'telephone',
                'crn',
                'tin',
                'administrative_units',
                'hidden_lock_change'
            ),
        }),
    )
    edit_fieldsets = (
        (_('Personal data'), {
            'classes': ('wide',),
            'fields': (
                'username', ('name'),
                'is_active',
                ('contact_first_name', 'contact_last_name',),
                'get_email',
                'get_main_telephone',
                'note',
                'administrative_units',
                'crn',
                'tin',
            ),
        }),
        (_('Contact data'), {
            'classes': ('wide', ),
            'fields': [
                ('street', 'city',),
                ('country', 'zip_code'),
                ('addressment', 'addressment_on_envelope'),
                'different_correspondence_address',
            ],
        }
         ),

        (_('Correspondence address'), {
             'classes': ('collapse', ),
             'fields': [
                 ('correspondence_street', 'correspondence_city',),
                 ('correspondence_country', 'correspondence_zip_code'),
             ],
         }
         ),
     )
    superuser_fieldsets = (
        (_('Rights and permissions'), {
            'classes': ('collapse',),
            'fields': [
                ('is_active',),
            ],
        }
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        if obj:
            self.form = CompanyProfileChangeForm
        else:
            self.form = CompanyProfileAddForm
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['language'].required = False
        form.request = request

        return form

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

    def add_view(self, request, form_url='', extra_context=None):
        """ crn or tin duplicity handler """
        data = request.POST
        if data.get('administrative_units'):
            try:
                if data.get('crn'):
                    company = CompanyProfile.objects.get(crn=data.get('crn'))
                elif data.get('tin'):
                    company = CompanyProfile.objects.get(tin=data.get('tin'))
                else:
                    raise CompanyProfile.DoesNotExist

                unit = AdministrativeUnit.objects.get(id=data.get('administrative_units'))
                company.administrative_units.add(unit)
                company.save()
                messages.warning(request, f'Company is in database already. You are able to make changes now.')
                url = reverse('admin:aklub_companyprofile_change', args=(company.pk,))
                return HttpResponseRedirect(url)

            except CompanyProfile.DoesNotExist:
                pass

        return super().add_view(request)


admin.site.register(DonorPaymentChannel, DonorPaymethChannelAdmin)
admin.site.register(UserYearPayments, UserYearPaymentsAdmin)
admin.site.register(NewUser, NewUserAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(MassCommunication, MassCommunicationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Recruiter, RecruiterAdmin)
admin.site.register(TaxConfirmation, TaxConfirmationAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(UserBankAccount, UserBankAccountAdmin)
# register all adminactions
actions.add_to_site(site)
