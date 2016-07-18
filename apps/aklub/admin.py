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
import csv
# Django imports
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect, HttpResponse
from daterange_filter.filter import DateRangeFilter
from import_export.admin import ImportExportModelAdmin
from related_admin import RelatedFieldAdmin
import django.forms
from django.utils.html import mark_safe
# Local models
from django.db.models import Sum
from .models import (
    UserInCampaign, UserProfile, Payment, Communication, Expense,
    TerminalCondition, UserYearPayments, NewUser, AccountStatements,
    AutomaticCommunication, MassCommunication, Condition, Campaign,
    Recruiter, Source, TaxConfirmation)
from . import mailing
from . import filters


def resave_action(self, request, queryset):
    for q in queryset:
        q.save()


def export_as_csv_action(description="Export selected objects as CSV file",
                         fields=None, exclude=None, header=True):
    """
    This function returns an export csv action
    'fields' and 'exclude' work like in django ModelForm
    'header' is whether or not to output the column names as the first row
    """
    def export_as_csv(modeladmin, request, queryset):
        """
        Generic csv export admin action.
        based on http://djangosnippets.org/snippets/2020/
        """
        assert not (fields and exclude)
        opts = modeladmin.model._meta
        if fields:
            field_names = fields
        else:
            field_names = set([field.name for field in opts.fields])
            if exclude:
                excludeset = set(exclude)
                field_names = field_names - excludeset
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % unicode(opts).replace('.', '_')
        writer = csv.writer(response)
        if header:
            writer.writerow(list(field_names))
        for obj in queryset:
            row = []
            for field in field_names:
                val = getattr(obj, field)
                if callable(val):
                    val = val()
                row.append(unicode(val).encode('utf-8'))
            writer.writerow(row)
        return response
    export_as_csv.short_description = description
    return export_as_csv


# -- INLINE FORMS --
class PaymentsInline(admin.TabularInline):
    model = Payment
    list_display = ('amount', 'person_name', 'date', 'paired_with_expected')
    extra = 5


class PaymentsInlineNoExtra(PaymentsInline):
    raw_id_fields = ('user',)
    extra = 0


class CommunicationInline(admin.TabularInline):
    model = Communication
    extra = 1
    readonly_fields = ('type', 'created_by', 'handled_by')

    def get_queryset(self, request):
        qs = super(CommunicationInline, self).get_queryset(request)
        qs = qs.filter(type__in=('individual', 'auto')).order_by('-date')
        return qs


class ExpenseInline(admin.TabularInline):
    model = Expense


def show_payments_by_year(self, request, queryset):
    payments = Payment.objects.filter(user__in=queryset)
    payment_dates = payments.dates('date', 'year')
    amount_string = ["%s: %s" % (
        date_year.year,
        payments.filter(date__year=date_year.year)
        .aggregate(Sum('amount'))['amount__sum'])
        for date_year in payment_dates]
    amount_string += (_("TOT.: %s") % payments.aggregate(Sum('amount'))['amount__sum'], )
    self.message_user(request, mark_safe("<br/>".join(amount_string)))
show_payments_by_year.short_description = _("Show payments by year")


class UserProfileAdmin(ImportExportModelAdmin):
    list_display = ('person_name', 'title_before', 'sex')
    raw_id_fields = ('recruiter',)


# -- ADMIN FORMS --
class UserInCampaignAdmin(ImportExportModelAdmin, RelatedFieldAdmin):
    list_display = ('person_name', 'userprofile__user__email', 'source', 'campaign',
                    'variable_symbol', 'registered_support_date',
                    'regular_payments_info', 'payment_delay', 'extra_payments',
                    'number_of_payments', 'total_contrib_string', 'regular_amount',
                    'userprofile__active', 'last_payment_date')
    date_hierarchy = 'registered_support'
    list_filter = [
        'regular_payments', 'userprofile__language', 'userprofile__active', 'userprofile__wished_information', 'old_account',
        'source', 'userprofile__campaigns', ('registered_support', DateRangeFilter), filters.EmailFilter,
        filters.UserConditionFilter, filters.UserConditionFilter1]
    search_fields = ['userprofile__user__first_name', 'userprofile__user__last_name', 'variable_symbol', 'email', 'userprofile__telephone']
    ordering = ('userprofile__user__last_name',)
    actions = ('send_mass_communication',
               show_payments_by_year,
               resave_action,
               export_as_csv_action(fields=(
                   'title_before', 'userprofile__user__first_name', 'userprofile__user__last_name', 'title_after', 'sex', 'userprofile__telephone', 'email',
                   'street', 'city', 'zip_code', 'variable_symbol', 'club_card_available',
                   'regular_payments', 'regular_frequency', 'registered_support',
                   'note', 'additional_information', 'userprofile__active', 'userprofile__language', 'recruiter')))
    save_as = True
    list_max_show_all = 10000
    list_per_page = 100
    inlines = [PaymentsInline, CommunicationInline]
    raw_id_fields = ('userprofile',)
    readonly_fields = ('verified_by',)
    filter_horizontal = ('campaigns',)  # broken in django pre-1.4
    fieldsets = [
        (_('Basic personal'), {
            'fields': [('firstname', 'surname'),
                       ('campaign',),
                       ('sex', 'language', 'active', 'public')]}),
        (_('Titles and addressments'), {
            'fields': [('title_before', 'title_after'),
                       ('addressment', 'addressment_on_envelope')],
            'classes': ['collapse']
            }),
        (_('Contacts'), {
            'fields': [('email', 'telephone'),
                       ('street', 'city', 'country'),
                       'zip_code', 'different_correspondence_address'],
            }),
        (_('Additional'), {
            'fields': ['knows_us_from',  'why_supports',
                       'field_of_work', 'additional_information'],
            'classes': ['collapse']}),
        (_('Support'), {
            'fields': ['variable_symbol',
                       'registered_support',
                       ('regular_payments', 'regular_frequency',
                        'regular_amount', 'expected_date_of_first_payment',
                        'exceptional_membership'),
                       'other_support', 'old_account']}),
        (_('Communications'), {
            'fields': ['wished_information', 'wished_tax_confirmation', 'wished_welcome_letter'],
            'classes': ['collapse']}),
        (_('Benefits'), {
            'fields': [('club_card_available', 'club_card_dispatched'),
                       'other_benefits'],
            'classes': ['collapse']}),
        (_('Notes'), {
            'fields': ['note', 'source', 'campaigns', 'recruiter', 'verified', 'verified_by', 'activity_points'],
            'classes': ['collapse']}),
        (_('Profile'), {
            'fields': ['profile_text', 'profile_picture'],
            'classes': ['collapse']}),
        ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('source__name')

    def save_formset(self, request, form, formset, change):
        # We need to save the request.user to inline Communication
        # the same as we do in CommunicationAdmin.save_model().
        # Unfortunatelly, save_model() doesn't work on CommunicationInline
        # so we need to workaround it using save_formset here.
        if not issubclass(formset.model, Communication):
            return super().save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:
                instance.created_by = request.user
            instance.handled_by = request.user
            instance.save()
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        if obj.verified and not obj.verified_by:
            obj.verified_by = request.user
        obj.save()

    def send_mass_communication(self, req, queryset):
        """Mass communication action

        Determine the list of user ids from the associated
        queryset and redirect us to insert form for mass communications
        with the send_to_users M2M field prefilled with these
        users."""
        selected = [str(e.pk) for e in queryset.all()]
        return HttpResponseRedirect("/admin/aklub/masscommunication/add/?send_to_users=%s" %
                                    (",".join(selected),))
    send_mass_communication.short_description = _("Send mass communication")


class UserYearPaymentsAdmin(UserInCampaignAdmin):
    list_display = ('person_name', 'userprofile__email', 'source',
                    'variable_symbol', 'registered_support_date',
                    'payment_total_by_year',
                    'userprofile__active', 'last_payment_date')
    list_filter = [
        ('payment__date', DateRangeFilter), 'regular_payments', 'userprofile__language', 'userprofile__active',
        'userprofile__wished_information', 'old_account', 'source', 'userprofile__campaigns',
        ('registered_support', DateRangeFilter), filters.EmailFilter, filters.UserConditionFilter, filters.UserConditionFilter1]

    def payment_total_by_year(self, obj):
        if self.from_date and self.to_date:
            return obj.payment_total_range(datetime.datetime.strptime(self.from_date, '%d.%m.%Y'), datetime.datetime.strptime(self.to_date, '%d.%m.%Y'))

    def changelist_view(self, request, extra_context=None):
        self.from_date = request.GET.get('drf__payment__date__gte', None)
        self.to_date = request.GET.get('drf__payment__date__lte', None)
        return super(UserYearPaymentsAdmin, self).changelist_view(request, extra_context=extra_context)


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'account_statement', 'amount', 'person_name', 'account_name', 'account', 'bank_code',
                    "transfer_note", "currency", "recipient_message", "operation_id", "transfer_type", "specification", "order_id",
                    'VS', 'SS', 'user_identification', 'type', 'paired_with_expected')
    fieldsets = [
        (_("Basic"), {
            'fields': [
                'user', 'date', 'amount',
                ('type', )]
            }),
        (_("Details"), {
            'fields': [('account', 'bank_code'),
                       ('account_name', 'bank_name'),
                       ('VS', 'KS', 'SS'),
                       'user_identification',
                       'account_statement']
            }),
        ]
    readonly_fields = ('account_statement',)
    raw_id_fields = ('user',)
    list_filter = ['type', 'date', filters.PaymentsAssignmentsFilter]
    date_hierarchy = 'date'
    search_fields = ['user__userprofile__user__last_name', 'user__userprofile__user__first_name', 'amount', 'VS', 'SS', 'user_identification']
    actions = (export_as_csv_action(fields=list_display),)


class NewUserAdmin(UserInCampaignAdmin):
    list_display = ('person_name', 'is_direct_dialogue',
                    'variable_symbol', 'regular_payments', 'registered_support',
                    'userprofile__recruiter', 'userprofile__active')


class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'dispatched', 'user', 'method',  'created_by', 'handled_by',
                    'user__regular_payments_info', 'user__payment_delay', 'user__extra_payments',
                    'date', 'type')
    raw_id_fields = ('user', )
    readonly_fields = ('type', 'created_by', 'handled_by', )
    list_filter = ['dispatched', 'send', 'date', 'method', 'type', ]
    date_hierarchy = 'date'
    ordering = ('-date',)

    fieldsets = [
        (_("Header"), {
            'fields': [('user', 'method', 'date')]
            }),
        (_("Content"), {
            'fields': ['subject',
                       ('summary', 'attachment'),
                       'note']
            }),
        (_("Sending"), {
            'fields': [('created_by', 'handled_by', 'send', 'dispatched')]
            }),
        ]

    def user__regular_payments_info(self, obj):
        return obj.user.regular_payments_info()

    def user__payment_delay(self, obj):
        return obj.user.payment_delay()

    def user__extra_payments(self, obj):
        return obj.user.extra_payments()

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
        qs = super(CommunicationAdmin, self).get_queryset(request)
        return qs.exclude(type='mass', dispatched='true')


class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'subject', 'condition', 'only_once', 'dispatch_auto')
    filter_horizontal = ('sent_to_users',)
    ordering = ('name',)

    def save_form(self, request, form, change):
        super(AutomaticCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        if "_continue" in request.POST and request.POST["_continue"] == "test_mail":
            mailing.send_mass_communication(obj, ["fake_user"], request.user, False)
            messages.info(request, _("Emails sent to following addreses: %s") % request.user.email)
        return obj


class MassCommunicationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ('name', 'date', 'method', 'subject')
    ordering = ('date',)

    filter_horizontal = ('send_to_users',)

    formfield_overrides = {
        django.db.models.CharField: {'widget': django.forms.TextInput(attrs={'size': '60'})},
    }

    fieldsets = [
        (_("Basic"), {
            'fields': [('name', 'method', 'date', 'note')]
            }),
        (_("Content"), {
            'fields': [('subject', 'subject_en'),
                       ('template', 'template_en'),
                       ('attachment', 'attach_tax_confirmation')]
            }),
        (_("Sending"), {
            'fields': ['send_to_users']
            }),
        ]

    def save_form(self, request, form, change):
        super(MassCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        if "_continue" in request.POST and request.POST["_continue"] == "test_mail":
            mailing.send_mass_communication(obj, ["fake_user"], request.user, False)
            messages.info(request, _("Emails sent to following addreses: %s") % request.user.email)

        if "_continue" in request.POST and request.POST["_continue"] == "send_mails":
            mailing.send_mass_communication(obj, obj.send_to_users.all(), request.user)
            # Sending was done, so revert the state of the 'send' checkbox back to False
            obj.date = datetime.datetime.now()
            obj.save()
            messages.info(request, _("Emails sent to following addreses: %s") % ", ".join([u.email for u in obj.send_to_users.all()]))
        return obj


class TerminalConditionInline(admin.TabularInline):
    model = TerminalCondition
    readonly_fields = ("variable_description",)
    extra = 0


class TerminalConditionAdmin(ImportExportModelAdmin):
    list_display = ('variable', 'operation', 'value', 'condition')


class ConditionAdmin(ImportExportModelAdmin):
    save_as = True
    list_display = ('name', 'as_filter', 'on_dashboard', 'operation', 'condition_string')
    filter_horizontal = ('conds',)
    inlines = [TerminalConditionInline, ]
    fieldsets = [
        (_("Description"), {
            'fields': ['name']
            }),
        (_("Operator"), {
            'fields': ['operation']
            }),
        (_("Logical conditions operands"), {
            'fields': ['conds']
            }),
        (_("Usage"), {
            'fields': ['as_filter', 'on_dashboard']
            }),
        ]

    ordering = ('name',)


def pair_variable_symbols(self, request, queryset):
    for account_statement in queryset:
        for payment in account_statement.payment_set.all():
            try:
                account_statement.pair_vs(payment)
                payment.save()
            except Exception as e:
                messages.error(request, _('Exception during pairing: %s' % e))
pair_variable_symbols.short_description = _("Pair payments with users based on variable symboles")


class AccountStatementsAdmin(admin.ModelAdmin):
    list_display = ('type', 'import_date', 'payments_count', 'csv_file', 'date_from', 'date_to')
    inlines = [PaymentsInlineNoExtra]
    readonly_fields = ('import_date', 'payments_count')
    fields = copy.copy(list_display)
    actions = (pair_variable_symbols,)

    def payments_count(self, obj):
        return obj.payment_set.count()

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'skipped_payments', None):
            skipped_payments_string = ', '.join(["%s %s (%s)" % (p['name'], p['surname'], p['email']) for p in obj.skipped_payments])
            messages.info(request, 'Skipped payments: %s' % skipped_payments_string)
        payments_without_user = ', '.join(["%s (%s)" % (p.account_name, p.user_identification) for p in obj.payment_set.all() if not p.user])
        if payments_without_user:
            messages.info(request, 'Payments without user: %s' % payments_without_user)
        obj.save()


class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'created', 'terminated', 'number_of_members', 'number_of_recruiters', 'acquisition_campaign', 'yield_total',
        'total_expenses', 'expected_monthly_income', 'return_of_investmensts', 'average_yield', 'average_expense')
    fields = (
        'created', 'terminated', 'name', 'description', 'acquisition_campaign', 'real_yield', 'number_of_members',
        'number_of_recruiters', 'yield_total', 'total_expenses', 'expected_monthly_income', 'return_of_investmensts', 'average_yield', 'average_expense')
    readonly_fields = (
        'number_of_members', 'number_of_recruiters', 'yield_total', 'total_expenses',
        'expected_monthly_income', 'return_of_investmensts', 'average_yield', 'average_expense')
    list_filter = ('acquisition_campaign', filters.ActiveCampaignFilter)
    inlines = (ExpenseInline, )


class RecruiterAdmin(admin.ModelAdmin):
    list_display = ('recruiter_id', 'person_name', 'email', 'telephone', 'problem', 'rating')
    list_filter = ('problem',)
    actions = (export_as_csv_action(fields=list(list_display)+['note']),)
    filter_horizontal = ('campaigns',)


class SourceAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'direct_dialogue')


class TaxConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'amount', 'file', 'user__regular_payments')
    ordering = ('user__userprofile__user__last_name', 'user__userprofile__user__first_name',)
    list_filter = ['year', 'user__regular_payments']
    search_fields = ('user__userprofile__user__last_name', 'user__firstname', 'user__variable_symbol',)
    actions = (export_as_csv_action(fields=('user', 'amount')),)
    list_max_show_all = 10000

    def generate(self, request):
        year = datetime.datetime.now().year - 1
        payed = Payment.objects.filter(date__year=year).exclude(type='expected').values_list('user_id', flat=True)
        donors = UserInCampaign.objects.filter(id__in=payed).order_by('userprofile__user__last_name')
        count = 0
        for d in donors:
            c = d.make_tax_confirmation(year)
            if c:
                count += 1
        messages.info(request, 'Generated %d tax confirmations' % count)
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


admin.site.register(UserInCampaign, UserInCampaignAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserYearPayments, UserYearPaymentsAdmin)
admin.site.register(NewUser, NewUserAdmin)
admin.site.register(Communication, CommunicationAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(MassCommunication, MassCommunicationAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(TerminalCondition, TerminalConditionAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Recruiter, RecruiterAdmin)
admin.site.register(TaxConfirmation, TaxConfirmationAdmin)
admin.site.register(Source, SourceAdmin)
