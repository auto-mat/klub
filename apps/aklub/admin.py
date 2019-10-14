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

import datetime

from admin_numeric_filter.admin import NumericFilterModelAdmin, RangeNumericFilter

from adminactions import actions, merge


from adminfilters.filters import RelatedFieldCheckBoxFilter

from advanced_filters.admin import AdminAdvancedFiltersMixin

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import site
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import CharField, Count, F, Max, Min, OuterRef, Q, Subquery, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import resolve
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
from import_export.widgets import CharWidget, ForeignKeyWidget

from import_export_celery.admin_actions import create_export_job_action

from interactions.admin import InteractionInline
from interactions.models import Interaction, InteractionType

from isnull_filter import isnull_filter

import large_initial

import nested_admin

from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicParentModelAdmin

from rangefilter.filter import DateRangeFilter

from related_admin import RelatedFieldAdmin

from smmapdfs.actions import make_pdfsandwich


from . import darujme, filters, mailing, tasks
from .custom_form_widgets import HtmlTemplateWidget
from .filters import ProfileTypeFilter, unit_admin_mixin_generator
from .forms import (
    CompanyProfileAddForm, CompanyProfileChangeForm, EventForm, TaxConfirmationForm, UnitUserProfileAddForm,
    UnitUserProfileChangeForm, UserCreateForm, UserUpdateForm,
)
from .models import (
    AccountStatements, AdministrativeUnit, ApiAccount, AutomaticCommunication, BankAccount,
    CompanyContact, CompanyProfile, DonorPaymentChannel, Event, Expense,
    MassCommunication, MoneyAccount, NewUser, Payment, Preference, Profile, ProfileEmail, Recruiter,
    Source, TaxConfirmation, Telephone, UserBankAccount,
    UserProfile,
)
from .profile_model_resources import (
    ProfileModelResource, get_polymorphic_parent_child_fields,
)
from .profile_model_resources_mixin import ProfileModelResourceMixin
from .utils import (
    check_annotate_filters, edit_donor_annotate_filter, 
    get_email_templates_names, sweet_text,
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
        if self.instance.id:
            self.fields['user_bank_account_char'].initial = self.instance.user_bank_account
        else:
            user_bank_accs = self.parent.userchannels
            if user_bank_accs.exclude(user_bank_account=None).values_list('user_bank_account').distinct().count() == 1:
                bank_acc = user_bank_accs.first()
                val = bank_acc.user_bank_account.bank_account_number if bank_acc.user_bank_account else ""
                self.fields['user_bank_account_char'].initial = val

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
        'get_dpch_details',
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
                    'get_dpch_details',
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

    def get_dpch_details(self, obj):
        url = reverse('admin:aklub_donorpaymentchannel_change', args=(obj.pk,))
        if obj.pk:
            redirect_button = mark_safe(
                                f"<a href='{url}'><input type='button' value='details'></a>"
                                )
        else:
            redirect_button = None
        return redirect_button
    get_dpch_details.short_description = _('DPCH details')

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
        'recipient_account',
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
                obj = ProfileEmail.objects.get(email=row['email'], user__polymorphic_ctype__model=UserProfile._meta.model_name).user
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
    contact_first_name = fields.Field(widget=CharWidget())
    contact_last_name = fields.Field(widget=CharWidget())

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

    def dehydrate_telephone(self, profile):
        contacts = profile.companycontact_set.order_by('id')
        if contacts:
            return ',\n'.join(contact.telephone if contact.telephone else "-" for contact in contacts)
        else:
            return "-"

    def dehydrate_email(self, profile):
        contacts = profile.companycontact_set.order_by('id')
        if contacts:
            return ',\n'.join(contact.email if contact.email else "-" for contact in contacts)
        else:
            return "-"

    def dehydrate_contact_first_name(self, profile):
        contacts = profile.companycontact_set.order_by('id')
        if contacts:
            return ',\n'.join(contact.contact_first_name if contact.contact_first_name else "-" for contact in contacts)
        else:
            return "-"

    def dehydrate_contact_last_name(self, profile):
        contacts = profile.companycontact_set.order_by('id')
        if contacts:
            return ',\n'.join(contact.contact_last_name if contact.contact_last_name else "-" for contact in contacts)
        else:
            return "-"

    def export_dehydrate_email(self, profile):
        try:
            email = CompanyContact.objects.get(company=profile, is_primary=True)
        except CompanyContact.DoesNotExist:
            email = CompanyContact.objects.filter(company=profile).first()
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
    fields = (
        'email', 'is_email_in_companyprofile', 'is_primary', 'note',
    )
    readonly_fields = ('is_email_in_companyprofile',)

    def is_email_in_companyprofile(self, obj):
        filter_kwargs = {'email': obj.email}
        if not self.form.request.user.has_perm('can_edit_all_units'):
            filter_kwargs['company__administrative_units__in'] = self.form.request.user.administrated_units.all()
            filter_kwargs['administrative_unit__in'] = self.form.request.user.administrated_units.all()

        contact = CompanyContact.objects.filter(**filter_kwargs)
        if contact.exists():
            company = contact.first().company
            url = reverse('admin:aklub_companyprofile_change', args=(company.pk,))
            icon = _boolean_icon(True)
            details = company.name or _("Details")
            return mark_safe(f'<a href="{url}">{icon} {details}</a>')
        else:
            return _boolean_icon(False)

    is_email_in_companyprofile.short_description = _("Is email in CompanyProfile")


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
    list_display = ('__str__', 'project_name', 'event', 'project_id', 'api_id', 'administrative_unit')

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
    list_display = ('__str__', 'id', 'bank_account', 'bank_account_number', 'administrative_unit')


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

    def get_donor_details(self, obj, *args):
        """ soft sort of donor payment channels """
        channels = obj.userchannels.all()
        results = []
        for channel in channels:
            if channel.regular_payments == 'regular':

                if self.filtered_events and str(channel.event.id) not in self.filtered_events:
                    continue

                if self.request.user.has_perm('aklub.can_edit_all_units'):
                    results.append(channel)
                # self.user_administrated_units is defined in queryset below
                elif channel.money_account.administrative_unit in self.user_administrated_units:
                    results.append(channel)
        return results

    def registered_support_date(self, obj):
        result = self.get_donor_details(obj)
        return ',\n'.join(d.registered_support.strftime('%Y-%m-%d') for d in result)

    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'userchannels__registered_support'

    def regular_amount(self, obj):
        result = self.get_donor_details(obj)
        return sweet_text(((str(d.regular_amount),) for d in result if d.regular_amount))
    regular_amount.short_description = _("Regular amount")
    regular_amount.admin_order_field = 'userchannels__regular_amount'

    def donor_delay(self, obj):
        def get_result(dpch):
            if isinstance(dpch.regular_payments_delay(), (bool,)):
                return _boolean_icon(True)
            else:
                return format_html("{} {} {}", mark_safe(_boolean_icon(False)), str(dpch.regular_payments_delay().days), 'days')

        result = sweet_text(((get_result(d),) for d in self.get_donor_details(obj)))
        return result

    donor_delay.short_description = _("Payment delay")
    donor_delay.admin_order_field = 'order_payment_delay'

    def donor_extra_money(self, obj):
        result = self.get_donor_details(obj)
        return sweet_text(((str(d.extra_money),) if d.extra_money else '-' for d in result))

    donor_extra_money.short_description = _("Extra money")
    donor_extra_money.admin_order_field = 'userchannels__extra_money'

    def donor_frequency(self, obj):
        result = self.get_donor_details(obj)
        return ',\n'.join(str(d.regular_frequency) for d in result)

    donor_frequency.short_description = _("Donor frequency")

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

    def get_first_payment_date(self, obj):
        return obj.first_payment_date
    get_first_payment_date.admin_order_field = 'first_payment_date'
    get_first_payment_date.short_description = _("Date of first payment")

    def get_event(self, obj):
        event = format_html_join(
            ', ', "<nobr>{}) {}</nobr>", ((d.event.id, d.event.name) for d in self.get_donor_details(obj) if d.event is not None),
            )
        return event
    get_event.admin_order_field = 'events'
    get_event.short_description = _("Events")

    def get_next_communication_date(self, obj):
        return obj.next_communication_date
    get_next_communication_date.short_description = _("Next Communication")
    get_next_communication_date.admin_order_field = 'next_communication_date'

    def make_tax_confirmation(self, request, queryset):
        request.method = None
        return ProfileAdmin.taxform(self, request, profiles=queryset)

    make_tax_confirmation.short_description = _("Make Tax Confirmation")

    actions = (
        make_tax_confirmation,
        create_export_job_action,
        send_mass_communication_action,
        )

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


class ProfileAdmin(
    filters.AdministrativeUnitAdminMixin,
    ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin,
    ProfileAdminMixin,
    UserAdmin, PolymorphicParentModelAdmin,
):
    polymorphic_list = True
    resource_class = ProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    base_model = Profile
    child_models = (UserProfile, CompanyProfile)
    list_display = ()
    change_list_template = "admin/aklub/profile_redirect.html"

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

    def taxform(self, request, *args, **kwargs):
        """ admin form view to generate tax confirmations"""
        if request.method == 'POST':
            data = request.POST
            parameters = (
                        data.get('year'),
                        data.getlist('profile'),
                        data.get('pdf_type')
            )
            tasks.generate_tax_confirmations.apply_async(args=parameters)
            messages.info(request, _('TaxConfirmations created'))
            return HttpResponseRedirect(reverse('admin:aklub_taxconfirmation_changelist'))
        else:
            from django.shortcuts import render
            form = TaxConfirmationForm(profiles=kwargs.get('profiles'), request=request)
            return render(
                request,
                'admin/aklub/profile_taxconfirmation.html',
                {'opts': self.model._meta, 'form': form},
            )

    def remove_contact_from_unit(self, request, pk=None):
        from django.shortcuts import render
        if request.method == "POST":
            profile = Profile.objects.get(pk=pk)
            if profile == request.user:
                messages.warning(request, _('You can not remove administrative unit from your own profile'))
            else:
                profile.administrative_units.remove(request.user.administrated_units.first())
                messages.info(request, _(f'Profile with ID "{pk}" was removed from your administrative unit'))

            if profile.polymorphic_ctype.model == 'userprofile':
                url = 'admin:aklub_userprofile_changelist'
            else:
                url = 'admin:aklub_companyprofile_changelist'

            return HttpResponseRedirect(reverse(url))
        else:
            profile = Profile.objects.get(pk=pk)
            if request.user.administrated_units.first() not in profile.administrative_units.all():
                messages.warning(request, _(f"profile with ID '{pk}' doesn't exist. Perhaps it was deleted?"))
                return HttpResponseRedirect(reverse('admin:index'))

            message = _("If you confirm, you wonˇt see this profile anymore ")
            HttpResponseRedirect(reverse('admin:aklub_taxconfirmation_changelist'))
            return render(
                    request,
                    'admin/aklub/profile_remove_contact_from_unit.html',
                    {'opts': self.model._meta, 'pk': pk, 'message': message},
                    )

    def get_urls(self):
        """ add extra view to admin """
        from django.conf.urls import url
        urls = super().get_urls()
        my_urls = [
            url(
                r'^(?P<pk>[0-9]+)/remove_contact_from_unit/$',
                self.admin_site.admin_view(self.remove_contact_from_unit),
                name='aklub_remove_contact_from_unit',
            ),
            url(
                r'taxform',
                self.admin_site.admin_view(self.taxform),
                name='aklub_profile_taxform',
            ),
        ]
        return my_urls + urls


class DonorPaymentChannelLoaderClass(BaseInstanceLoader):
    def get_instance(self, row):
        try:
            event = Event.objects.get(id=row.get('event'))
            money_account = BankAccount.objects.get(id=row.get('money_account'))

            obj = DonorPaymentChannel.objects.get(
                                            user_id=row.get('user'),
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


class DonorPaymentChannelWidget(ForeignKeyWidget):
    """ Handle ForeignKey no exist error """
    def get_queryset(self, value, row):
        values = self.model.objects.filter(id=value)
        if values:
            return values
        else:
            raise ValueError(" This id doesn't exist")


class DonorPaymentChannelResource(ModelResource):
    profile_type = fields.Field()
    email = fields.Field()
    user_bank_account = fields.Field()
    event = fields.Field(attribute='event', widget=DonorPaymentChannelWidget(Event))
    money_account = fields.Field(attribute='money_account', widget=DonorPaymentChannelWidget(MoneyAccount))

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
        if not row.get('profile_type') or row.get('profile_type') not in ['u', 'c']:
            raise ValidationError({'profile_type': 'Insert "c" or "u" (company/user)'})
        row['email'] = row['email'].lower()
        try:
            if row.get('profile_type') == 'u':
                row['user'] = ProfileEmail.objects.get(email=row['email']).user.id
            else:
                row['user'] = CompanyContact.objects.get(email=row['email']).company.id
        except (ProfileEmail.DoesNotExist, CompanyContact.DoesNotExist):
            raise ValidationError({"email": "Company/User with this email doesn't exist"})

    def import_obj(self, obj, data, dry_run):
        super(ModelResource, self).import_obj(obj, data, dry_run)
        if data.get('user_bank_account'):
            user_bank_acc, _ = UserBankAccount.objects.get_or_create(bank_account_number=data.get('user_bank_account'))
            obj.user_bank_account = user_bank_acc
            obj.save()
        return obj

    def dehydrate_user_bank_account(self, donor):
        if donor.user_bank_account:
            obj = donor.user_bank_account.bank_account_number
        else:
            obj = ''
        return obj

    def dehydrate_email(self, donor):
        if hasattr(donor, 'user'):
            if donor.user.polymorphic_ctype.model == UserProfile._meta.model_name:
                try:
                    email = donor.user.userprofile.profileemail_set.get(is_primary=True)
                except ProfileEmail.DoesNotExist:
                    email = donor.user.userprofile.profileemail_set.first()
            else:
                try:
                    email = donor.user.companyprofile.companycontact_set.get(is_primary=True)
                except CompanyContact.DoesNotExist:
                    email = donor.user.companyprofile.companycontact_set.first()
            return email.email
        return ''

    def dehydrate_user(self, donor):
        if hasattr(donor, 'user'):
            return donor.user.username


# -- ADMIN FORMS --
class DonorPaymetChannelAdmin(
    unit_admin_mixin_generator('user__administrative_units'),
    ImportExportMixin,
    AdminAdvancedFiltersMixin,
    RelatedFieldAdmin,
    nested_admin.NestedModelAdmin,
):
    list_display = (
        'get_name',
        'get_email',
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
    )
    advanced_filter_fields = (
        'user__userprofile__first_name',
        'user__userprofile__last_name',
        'user__email',
        ('campaign__name', _("Campaign name")),
        'VS',
        'SS',
        'registered_support',
        'regular_payments',
        'extra_money',
        'number_of_payments',
        'payment_total',
        'regular_amount',
        'user__is_active',
        'last_payment__date',
    )
    date_hierarchy = 'registered_support'
    list_filter = [
        ProfileTypeFilter,
        'regular_payments',
        'user__language',
        'user__is_active',
        'old_account',
        ('event', RelatedFieldCheckBoxFilter),
        ('registered_support', DateRangeFilter),
    ]
    search_fields = [
        'user__companyprofile__name',
        'user__companyprofile__crn',
        'user__companyprofile__tin',
        'user__userprofile__first_name',
        'user__userprofile__last_name',
        'VS',
        'SS',
        'user__email',
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
    raw_id_fields = (
        'user',
    )
    readonly_fields = (
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

    def get_queryset(self, request):
        """
        The annotate hacking in this query is because django-polymorphic doesnt support
        prefetch_related and select_related in normal way!
        Then we want to avoid hitting DB in every list_row
        """
        primary_email_user = ProfileEmail.objects.filter(user=OuterRef('user'), is_primary=True)
        primary_email_company = CompanyContact.objects.filter(
            company=OuterRef('user'),
            administrative_unit=OuterRef('money_account__administrative_unit'),
            is_primary=True,
        )

        qs = super().get_queryset(request)\
            .annotate(
                last_name=F("user__userprofile__last_name"),
                first_name=F("user__userprofile__first_name"),
                company_name=F("user__companyprofile__name"),
                # TODO: profile_type shoud not be there, but dpch returns user parent model instead of child...
                # and we are not able to recognize child without hitting db.
                profile_type=F("user__userprofile__polymorphic_ctype__model"),
                email_address_user=Subquery(primary_email_user.values('email')),
                email_address_company=Subquery(primary_email_company.values('email')),

        )
        return qs

    def user_note(self, obj):
        return obj.user.note

    def user_telephone_url(self, obj):
        return obj.user.telephone_url()

    def get_email(self, obj):
        if obj.profile_type == UserProfile._meta.model_name:
            return obj.email_address_user
        else:
            return obj.email_address_company

    def get_name(self, obj):
        if obj.profile_type == UserProfile._meta.model_name:
            if obj.first_name or obj.last_name:
                return f"{obj.first_name} {obj.last_name}"
            else:
                return '-'
        else:
            return obj.company_name or '-'


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


class PaymentWidget(ForeignKeyWidget):
    """ Handle ForeignKey no exist error """
    def get_queryset(self, value, row):
        values = self.model.objects.filter(id=value)
        if values:
            return values
        else:
            raise ValueError("This id doesn't exist")


class PaymentResource(ModelResource):
    recipient_account = fields.Field(attribute='recipient_account', widget=PaymentWidget(MoneyAccount))
    user_donor_payment_channel = fields.Field(attribute='user_donor_payment_channel', widget=PaymentWidget(DonorPaymentChannel))

    class Meta:
        model = Payment
        fields = (
            'recipient_account', 'date', 'amount', 'account' 'bank_code', 'VS', 'VS2', 'SS', 'KS',
            'BIC', 'user_identification', 'type', 'done_by', 'account_name', 'bank_name', 'transfer_note',
            'currency', 'recipient_message', 'operation_id', 'transfer_type', 'specification',
            'order_id', 'user_donor_payment_channel', 'created', 'updated',
                  )
        clean_model_instances = True
        import_id_fields = []  # must be empty or library take field id as default
    """
    TODO: add payment_pair from account_statement model to pair payments
        import_obj is the way
    """


class PaymentAdmin(
    ImportExportMixin,
    RelatedFieldAdmin,
):
    def get_full_name(self, obj):
        if obj.company_name:
            return obj.company_name
        else:
            return f"{obj.first_name} {obj.last_name}"

    get_full_name.short_description = _("name")

    actions = (add_user_bank_acc_to_dpch, payment_pair_action, payment_request_pair_action)
    resource_class = PaymentResource
    list_display = (
        'id',
        'date',
        'amount',
        'user_donor_payment_channel',
        'get_full_name',
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
    list_editable = ('user_donor_payment_channel',)
    fieldsets = [
        (_("Basic"), {
            'fields': [
                'user_donor_payment_channel', 'date', 'amount',
                ('type',),
                ('recipient_account',),
                ('our_note',),
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

    def get_queryset(self, request):
        """
        Display all payments for request under adminstrated unit where:
            payment's money_account_administrative_unit (if exist)
            payments's account_statement_administrative_unit (if exist) (old reason)
            payments' donor_payment_channel_money_account_administrative_unit (old reason)

        The annotate hacking in this query is because django-polymorphic doesnt support
        prefetch_related and select_related in normal way!
        Then we want to avoid hitting DB in every list_row
        """
        qs = super().get_queryset(request)\
                    .select_related('user_donor_payment_channel')\
                    .annotate(
                        last_name=F("user_donor_payment_channel__user__userprofile__last_name"),
                        first_name=F("user_donor_payment_channel__user__userprofile__first_name"),
                        company_name=F("user_donor_payment_channel__user__companyprofile__name"),
                    )

        if not request.user.has_perm('aklub.can_edit_all_units'):
            administrated_unit = request.user.administrated_units.first()
            qs = qs.filter(
                    Q(recipient_account__administrative_unit=administrated_unit) |
                    Q(user_donor_payment_channel__money_account__administrative_unit=administrated_unit) |
                    Q(account_statement__administrative_unit=administrated_unit),
                )
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "recipient_account":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs["queryset"] = MoneyAccount.objects.filter(administrative_unit=request.user.administrated_units.first())
            else:
                kwargs["queryset"] = MoneyAccount.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request, *args, **kwargs):
        """
        if filter on current dpch is active -> fill dpch field in add form
        """
        initial = super().get_changeform_initial_data(request)
        if initial and 'user_donor_payment_channel' in initial.get('_changelist_filters'):
            get_data = initial['_changelist_filters'].split('&')
            dpch = [dpch for dpch in get_data if 'user_donor_payment_channel' in dpch][0].split('=')[1]
            return {
                'user_donor_payment_channel': dpch,
            }


class NewUserAdmin(DonorPaymetChannelAdmin):
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
    hidden_template = forms.CharField(widget=forms.HiddenInput(), required=False)
    hidden_template_en = forms.CharField(widget=forms.HiddenInput(), required=False)
    template_textarea = forms.CharField(widget=forms.Textarea(), required=False)
    template_en_textarea = forms.CharField(widget=forms.Textarea(), required=False)

    class Meta:
        model = MassCommunication
        fields = '__all__'
        widgets = {
            'template': HtmlTemplateWidget(
                attrs={
                    'class': 'template',
                },
            ),
            'template_en': HtmlTemplateWidget(
                attrs={
                    'class': 'template',
                },
            ),
        }

    class Media:
        js = (
            'jquery/dist/jquery.min.js',
            'jquery-ui/jquery-ui.min.js',
            'jquery.inlineStyler/jquery.inlineStyler.min.js',
            'webui-popover/dist/jquery.webui-popover.min.js',
            'aklub/js/csrf_token.js',
            'aklub/js/html_template.js',
            'aklub/js/form_field_widget_init.js',
        )
        css = {
            'all': (
                'jquery-ui/themes/base/jquery-ui.min.css',
                'webui-popover/dist/jquery.webui-popover.min.css',
                'aklub/css/template.css',
            )
        }

    def __init__(self, *args, **kwargs):
        super(MassCommunicationForm, self).__init__(*args, **kwargs)
        self.fields['template_name'] = forms.ChoiceField(
            choices=get_email_templates_names(),
            required=False
        )
        self.fields['template_en_name'] = forms.ChoiceField(
            choices=get_email_templates_names(),
            required=False
        )

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


class MassCommunicationAdmin(unit_admin_mixin_generator('administrative_unit'), large_initial.LargeInitialMixin, admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'date', 'method_type', 'subject')
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

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "send_to_users":
            # lets make it a little easier for superadmin (if he has administrated_units)
            if not request.user.has_perm('aklub.can_edit_all_units'):
                users_ids = Preference.objects.filter(
                                            administrative_unit=request.user.administrated_units.first(),
                                            send_mailing_lists=True,
                            ).values_list('user__id', flat=True)

                kwargs["queryset"] = Profile.objects.filter(
                                            is_active=True,
                                            id__in=users_ids,
                                     ).distinct()
            else:
                kwargs["queryset"] = Profile.objects.filter(is_active=True).distinct()
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
    list_filter = (
        'type',
        ('payment__date', DateRangeFilter),
    )
    inlines = [PaymentsInlineNoExtra]
    readonly_fields = ('import_date', 'payments_count', 'paired_payments', 'pair_log')
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
    form = EventForm
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


class RecruiterAdmin(admin.ModelAdmin):
    list_display = ('recruiter_id', 'person_name', 'email', 'telephone', 'problem', 'rating')
    list_filter = ('problem', 'campaigns')
    filter_horizontal = ('campaigns',)


class SourceAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'direct_dialogue')


class TaxConfirmationAdmin(
            unit_admin_mixin_generator('pdf_type__pdfsandwichtypeconnector__administrative_unit'),
            admin.ModelAdmin,
            ):

    def batch_download(self, request, queryset):
        links = []
        for q in queryset:
            file_field = q.taxconfirmationpdf_set.get().pdf
            if file_field:
                links.append(file_field.url)
        return HttpResponse("\n".join(links), content_type='text/plain')

    batch_download.short_description = _("generate download links for pdf files")

    list_display = (
        'get_name',
        'get_email',
        'year',
        'amount',
        'get_pdf',
        'get_administrative_unit',
        'pdf_type'
    )
    ordering = (
        'user_profile__userprofile__last_name',
        'user_profile__userprofile__first_name',
        'user_profile__companyprofile__name',
    )
    list_filter = [
        'year',
        'pdf_type',
        'pdf_type__pdfsandwichtypeconnector__administrative_unit',
        'pdf_type__pdfsandwichtypeconnector__profile_type',
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

    readonly_fields = ['get_pdf', 'get_email', 'pdf_type', 'get_administrative_unit']
    fields = ['user_profile', 'year', 'amount', 'get_pdf', 'pdf_type']

    def get_queryset(self, request):
        """
        The annotate hacking in this query is because django-polymorphic doesnt support
        prefetch_related and select_related in normal way!
        Then we want to avoid hitting DB in every list_row
        """
        primary_email_user = ProfileEmail.objects.filter(user=OuterRef('user_profile_id'), is_primary=True)
        primary_email_company = CompanyContact.objects.filter(
            company=OuterRef('user_profile_id'),
            administrative_unit=OuterRef('pdf_type__pdfsandwichtypeconnector__administrative_unit'),
            is_primary=True,
        )

        qs = super().get_queryset(request)\
            .select_related(
                'pdf_type__pdfsandwichtypeconnector__administrative_unit',
                'user_profile__companyprofile',
                'user_profile__userprofile',
                'pdf_type__pdfsandwichtypeconnector',
            )\
            .annotate(
                last_name=F("user_profile__userprofile__last_name"),
                first_name=F("user_profile__userprofile__first_name"),
                company_name=F("user_profile__companyprofile__name"),
                # TODO: profile_type shoud not be there, but dpch returns user parent model instead of child...
                # and we are not able to recognize child without hitting db.
                profile_type=F("user_profile__polymorphic_ctype__model"),
                email_address_user=Subquery(primary_email_user.values('email')),
                email_address_company=Subquery(primary_email_company.values('email')),
        )
        return qs

    def get_email(self, obj):
        if obj.profile_type == UserProfile._meta.model_name:
            return obj.email_address_user
        else:
            return obj.email_address_company
    get_email.short_description = _("Main email")

    def get_administrative_unit(self, obj):
        try:
            au = obj.pdf_type.pdfsandwichtypeconnector.administrative_unit.name
        except AttributeError:
            au = None
        return au
    get_administrative_unit.short_description = _("Administrative Unit")

    def get_name(self, obj):
        if obj.company_name:
            return obj.company_name or '-'
        else:
            if obj.first_name or obj.last_name:
                return f"{obj.first_name} {obj.last_name}"
            else:
                return "-"
    get_name.short_description = _("Name")


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
            inline.form.parent = obj
            yield inline.get_formset(request, obj), inline

    readonly_fields = (
        'userattendance_links', 'date_joined', 'last_login', 'get_main_telephone',
        'get_email', 'regular_amount', 'donor_delay', 'registered_support_date',
        'donor_frequency', 'total_payment', 'donor_extra_money',
    )

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        if not obj:
            inlines = []
        return inlines


@admin.register(UserProfile)
class UserProfileAdmin(
        child_redirect_mixin('userprofile'), filters.AdministrativeUnitAdminMixin,
        ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin, ProfileAdminMixin,
        BaseProfileChildAdmin, NumericFilterModelAdmin,
):
    """ User profile polymorphic admin model child class """
    base_model = UserProfile
    show_in_index = True
    save_on_top = True
    resource_class = UserProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    change_form_template = "admin/aklub/profile_changeform.html"
    inlines = [
        PreferenceInline, ProfileEmailInline, TelephoneInline,
        DonorPaymentChannelInline, InteractionInline,
    ]
    list_display = (
        'person_name',
        'username',
        'get_email',
        'get_main_telephone',
        'get_administrative_units',
        'get_event',
        'date_joined',
        # 'get_next_communication_date',
        'get_sum_amount',
        'get_payment_count',
        'get_first_payment_date',
        'get_last_payment_date',
        'regular_amount',
        'donor_delay',
        'donor_extra_money',

    )

    actions = () + ProfileAdminMixin.actions

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
        filters.PreferenceMailingListAllowed,
        isnull_filter('userchannels__payment', _('Has any payment'), negate=True),
        ('userchannels__extra_money', RangeNumericFilter),
        ('userchannels__regular_amount', RangeNumericFilter),
        'userchannels__regular_frequency',
        'userchannels__regular_payments',
        ('userchannels__registered_support', DateRangeFilter),
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'language',
        ('userchannels__last_payment__date', DateRangeFilter),
        filters.IsUserInCompanyProfile,
        ('userchannels__event__id', filters.ProfileMultiSelectDonorEvent),
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
                ('get_email',),
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

    def get_email(self, obj):
        emails = obj.get_email()
        if resolve(self.request.path_info).url_name == 'aklub_userprofile_change':
            # add anchor in changeform
            emails = mark_safe('<a href="#profileemail_set-group">%(detail)s</a><br>' % {'detail': _('Details')}) + emails
        return emails
    get_email.short_description = _("Emails")

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

    def get_queryset(self, request, *args, **kwargs):
        # save request user's adminsitratived_unit here, so we dont have to peek in every loop
        self.user_administrated_units = request.user.administrated_units.all()

        donor_filter = edit_donor_annotate_filter(self, request)

        filter_kwargs = {}
        filter_kwargs = check_annotate_filters(self.list_display, request, filter_kwargs)
        # annotate_kwargs = check_annotate_subqueries(self, request)
        if request.user.has_perm('aklub.can_edit_all_units'):
            queryset = super().get_queryset(request, *args, **kwargs).prefetch_related(
                    'telephone_set',
                    'profileemail_set',
                    'administrative_units',
                    'userchannels__event',
                    'interaction_set',
                ).annotate(
                    sum_amount=Sum('userchannels__payment__amount', filter=Q(**donor_filter)),
                    payment_count=Count('userchannels__payment', filter=Q(**donor_filter)),
                    last_payment_date=Max('userchannels__payment__date', filter=Q(**donor_filter)),
                    first_payment_date=Min('userchannels__payment__date', filter=Q(**donor_filter)),
                    # **annotate_kwargs,
                    **filter_kwargs,
                )
        else:
            donor_filter['userchannels__money_account__administrative_unit'] = self.user_administrated_units.first()
            queryset = super().get_queryset(request, *args, **kwargs).prefetch_related(
                    'telephone_set',
                    'profileemail_set',
                    'administrative_units',
                    'userchannels__event',
                    'userchannels__money_account__administrative_unit',
                    'interaction_set',
                ).annotate(
                    sum_amount=Sum('userchannels__payment__amount', filter=Q(**donor_filter)),
                    payment_count=Count('userchannels__payment', filter=Q(**donor_filter)),
                    last_payment_date=Max('userchannels__payment__date', filter=Q(**donor_filter)),
                    first_payment_date=Min('userchannels__payment__date', filter=Q(**donor_filter)),
                    # **annotate_kwargs,
                    **filter_kwargs,
                )

        return queryset


class CompanyContactInline(admin.TabularInline):
    model = CompanyContact
    extra = 0
    can_delete = True
    show_change_link = True
    fields = (
        'contact_first_name', 'contact_last_name', 'email', 'is_email_in_userprofile', 'telephone',
        'is_primary', 'note', 'administrative_unit',
    )
    readonly_fields = ('is_email_in_userprofile',)

    def is_email_in_userprofile(self, obj):
        filter_kwargs = {'email': obj.email}
        if not self.form.request.user.has_perm('can_edit_all_units'):
            filter_kwargs['user__administrative_units__in'] = self.form.request.user.administrated_units.all()
        email = ProfileEmail.objects.filter(**filter_kwargs)
        if email.exists():
            email = email.first()
            url = reverse('admin:aklub_userprofile_change', args=(email.user.pk,))
            icon = _boolean_icon(True)
            details = _("Details")
            return mark_safe(f'<a href="{url}">{icon} {details}</a>')
        else:
            return _boolean_icon(False)
    is_email_in_userprofile.short_description = _("Is email in userprofile")

    def get_queryset(self, request):
        if not request.user.has_perm('aklub.can_edit_all_units'):
            queryset = CompanyContact.objects.filter(administrative_unit__in=request.user.administrated_units.all())
        else:
            queryset = super().get_queryset(request)
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "administrative_unit":
            if not request.user.has_perm('aklub.can_edit_all_units'):
                kwargs['queryset'] = request.user.administrated_units.all()
            else:
                kwargs['queryset'] = AdministrativeUnit.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(
        child_redirect_mixin('companyprofile'), filters.AdministrativeUnitAdminMixin,
        ImportExportMixin, RelatedFieldAdmin, AdminAdvancedFiltersMixin,
        ProfileAdminMixin, BaseProfileChildAdmin, NumericFilterModelAdmin,
):
    """ Company profile polymorphic admin model child class """
    base_model = CompanyProfile
    show_in_index = True
    save_on_top = True
    resource_class = CompanyProfileResource
    import_template_name = "admin/import_export/userprofile_import.html"
    change_form_template = "admin/aklub/profile_changeform.html"
    inlines = [
        PreferenceInline, CompanyContactInline,
        DonorPaymentChannelInline, InteractionInline,
    ]
    list_display = (
        'name',
        'crn',
        'tin',
        'get_contact_name',
        'get_company_email',
        'get_company_telephone',
        'get_administrative_units',
        'get_event',
        'date_joined',
        # 'get_next_communication_date',
        'get_sum_amount',
        'get_payment_count',
        'get_first_payment_date',
        'get_last_payment_date',
        'regular_amount',
        'donor_delay',
        'donor_extra_money',
    )

    actions = () + ProfileAdminMixin.actions
    readonly_fields = BaseProfileChildAdmin.readonly_fields + ('get_company_email', 'get_company_telephone')
    advanced_filter_fields = (
        'email',
        'companycontact__telephone',
        'name',
        'crn',
        'tin',
        'is_staff',
        'date_joined',
        'last_login',
        ('userchannels__event__name', _("Jméno kampaně")),
    )
    search_fields = (
        'name',
        'companycontact__telephone',
        'companycontact__email',
        'companycontact__contact_first_name',
        'companycontact__contact_last_name',
    )
    list_filter = (
        filters.PreferenceMailingListAllowed,
        isnull_filter('userchannels__payment', _('Has any payment'), negate=True),
        ('userchannels__extra_money', RangeNumericFilter),
        ('userchannels__regular_amount', RangeNumericFilter),
        'userchannels__regular_frequency',
        'userchannels__regular_payments',
        ('userchannels__registered_support', DateRangeFilter),
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
        'language',
        ('userchannels__last_payment__date', DateRangeFilter),
        ('userchannels__event__id', filters.ProfileMultiSelectDonorEvent),
        filters.RegularPaymentsFilter,
        filters.EmailFilter,
        filters.TelephoneFilter,
        UserConditionFilter, UserConditionFilter1,
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
                'get_company_email',
                'get_company_telephone',
                'note',
                'crn',
                'tin',
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
                ('is_active',),
            ],
        }
        ),
    )

    def get_company_email(self, obj):
        if self.request.user.has_perm('aklub.can_edit_all_units'):
            emails = obj.get_email()
        else:
            com = [c for c in obj.companycontact_set.all() if c.administrative_unit_id in self.user_administrated_units_ids]
            emails = obj.get_email(com)
        # if in edit form add anchor to inlines
        if resolve(self.request.path_info).url_name == 'aklub_companyprofile_change':
            emails = mark_safe('<a href="#companycontact_set-group">%(detail)s</a><br>' % {'detail': _('Details')}) + emails
        return emails
    get_company_email.short_description = _("Emails")

    def get_company_telephone(self, obj):

        if self.request.user.has_perm('aklub.can_edit_all_units'):
            return obj.get_main_telephone()
        else:
            com = [c for c in obj.companycontact_set.all() if c.administrative_unit_id in self.user_administrated_units_ids]
            return obj.get_main_telephone(com)

    get_company_telephone.short_description = _("Main telephone")

    def get_contact_name(self, obj):
        if self.request.user.has_perm('aklub.can_edit_all_units'):
            return obj.get_main_contact_name()
        else:
            com = [c for c in obj.companycontact_set.all() if c.administrative_unit_id in self.user_administrated_units_ids]
            return obj.get_main_contact_name(com)

    get_contact_name.short_description = _("Contact Name")

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
                messages.warning(request, 'Company is in database already. You are able to make changes now.')
                url = reverse('admin:aklub_companyprofile_change', args=(company.pk,))
                return HttpResponseRedirect(url)

            except CompanyProfile.DoesNotExist:
                pass

        return super().add_view(request)

    def get_queryset(self, request, *args, **kwargs):
        # save request user's adminsitratived_unit here, so we dont have to peek in every loop
        self.user_administrated_units = request.user.administrated_units.all()
        self.user_administrated_units_ids = request.user.administrated_units.all().values_list('id', flat=True)

        donor_filter = edit_donor_annotate_filter(self, request)

        filter_kwargs = {}
        filter_kwargs = check_annotate_filters(self.list_display, request, filter_kwargs)
        # annotate_kwargs = check_annotate_subqueries(self, request)
        if request.user.has_perm('aklub.can_edit_all_units'):
            queryset = super().get_queryset(request, *args, **kwargs).prefetch_related(
                    'companycontact_set',
                    'administrative_units',
                    'userchannels__event',
                ).annotate(
                    sum_amount=Sum('userchannels__payment__amount', filter=Q(**donor_filter)),
                    payment_count=Count('userchannels__payment', filter=Q(**donor_filter)),
                    last_payment_date=Max('userchannels__payment__date', filter=Q(**donor_filter)),
                    first_payment_date=Min('userchannels__payment__date', filter=Q(**donor_filter)),
                    # **annotate_kwargs,
                    **filter_kwargs,
                )
        else:
            donor_filter['userchannels__money_account__administrative_unit'] = self.user_administrated_units.first()
            queryset = super().get_queryset(request, *args, **kwargs).prefetch_related(
                    'companycontact_set',
                    'administrative_units',
                    'userchannels__event',
                    'userchannels__money_account__administrative_unit',
                ).annotate(
                    sum_amount=Sum('userchannels__payment__amount', filter=Q(**donor_filter)),
                    payment_count=Count('userchannels__payment', filter=Q(**donor_filter)),
                    last_payment_date=Max('userchannels__payment__date', filter=Q(**donor_filter)),
                    first_payment_date=Min('userchannels__payment__date', filter=Q(**donor_filter)),
                    # **annotate_kwargs,
                    **filter_kwargs,
                )

        return queryset


admin.site.register(DonorPaymentChannel, DonorPaymetChannelAdmin)
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
