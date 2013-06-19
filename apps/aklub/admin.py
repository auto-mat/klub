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
import django.forms
# Local models
from aklub.models import *
from aklub import mailing
import filters

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
        response = HttpResponse(mimetype='text/csv')
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
    extra = 0

class CommunicationInline(admin.TabularInline):
    model = Communication
    extra = 1
    readonly_fields = ('type', 'created_by', 'handled_by',)

class ExpenseInline(admin.TabularInline):
    model = Expense

# -- ADMIN FORMS --
class UserAdmin(admin.ModelAdmin):
    list_display = ('person_name', 
                    'variable_symbol', 'registered_support_date',
                    'regular_payments_info', 
                    'number_of_payments', 'total_contrib', 'regular_amount',
                    'active', 'last_payment_date')
    list_filter = ['regular_payments', 'language', 'active',  'source', 'campaigns', filters.UserConditionFilter]
    search_fields = ['firstname', 'surname', 'variable_symbol']
    ordering = ('surname',)
    actions = ('send_mass_communication',
               export_as_csv_action(fields=(
                'title_before', 'firstname', 'surname', 'title_after', 'sex', 'telephone', 'email',
                'street', 'city', 'zip_code', 'variable_symbol', 'club_card_available',
                'regular_payments', 'regular_frequency', 'registered_support',
                'note', 'additional_information', 'active', 'language', 'recruiter')
            ))
    save_as = True
    inlines = [PaymentsInline, CommunicationInline]
    raw_id_fields = ('recruiter',)
    readonly_fields = ('verified_by',)
    filter_horizontal = ('campaigns',) # broken in django pre-1.4
    fieldsets = [
        ('Basic personal', {
                'fields': [('firstname', 'surname'),
                           ('sex', 'language', 'active', 'public')]}),
        ('Titles and addressments', {
                'fields': [('title_before', 'title_after'),
                           ('addressment', 'addressment_on_envelope')],
                'classes': ['collapse']
                }),
        ('Contacts', {
                'fields': [('email', 'telephone'),
                           ('street', 'city', 'country'),
                           'zip_code'],
                }),
        ('Additional', {
                'fields': ['knows_us_from',  'why_supports',
                           'field_of_work', 'additional_information'],
                'classes': ['collapse']}),
        ('Support', {
                'fields': ['variable_symbol',
                           'registered_support',                           
                           ('regular_payments', 'regular_frequency',
                            'regular_amount', 'expected_date_of_first_payment',
                            'exceptional_membership'),
                           'other_support']}),
        ('Communication', {
                'fields': ['wished_information', 'wished_tax_confirmation', 'wished_welcome_letter'],
                'classes': ['collapse']}),
        ('Benefits', {
                'fields': [('club_card_available', 'club_card_dispatched'),
                           'other_benefits'],
                'classes': ['collapse']}),
        ('Note', {
                'fields': ['note', 'source', 'campaigns', 'recruiter', 'verified', 'verified_by'],
                'classes': ['collapse']}),
        ('Profile', {
                'fields': ['profile_text', 'profile_picture'],
                'classes': ['collapse']}),
        ]

    def queryset(self, request):
        qs = super(UserAdmin, self).queryset(request)
        return qs.annotate(**User.annotations)

    def save_formset(self, request, form, formset, change):
	# We need to save the request.user to inline Communication
	# the same as we do in CommunicationAdmin.save_model().
	# Unfortunatelly, save_model() doesn't work on CommunicationInline
	# so we need to workaround it using save_formset here.
        if not issubclass(formset.model, Communication):
            return super(UserAdmin, self).save_formset(request, form, formset, change)
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
        return HttpResponseRedirect("/aklub/masscommunication/add/?send_to_users=%s" %
                                    (",".join(selected),))
    send_mass_communication.short_description = _("Send mass communication")    

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'amount', 'person_name', 'account', 'bank_code',
                    'VS', 'user_identification', 'type', 'paired_with_expected')
    fieldsets = [
        (_("Basic"), {
                'fields' : ['user', 'date', 'amount',
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
    search_fields = ['user__surname', 'user__firstname', 'amount', 'VS', 'user_identification']
    actions = (export_as_csv_action(fields=list_display),)

class NewUserAdmin(UserAdmin):
    list_display = ('person_name', 'is_direct_dialogue',
                    'variable_symbol', 'regular_payments', 'registered_support',
                    'recruiter', 'active')

class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'dispatched', 'user', 'method',  'created_by', 'handled_by',
                    'date', 'type')
    raw_id_fields = ('user',)
    readonly_fields = ('type', 'created_by', 'handled_by',)
    list_filter = [ 'dispatched', 'send', 'date', 'method', 'type',]
    date_hierarchy = 'date'
    ordering = ('-date',)

    fieldsets = [
        (_("Header"), {
                'fields' : [('user', 'method', 'date')]
                }),
        (_("Content"), {
                'fields': ['subject',
                           ('summary', 'attachment'),
                           'note']
                }),
        (_("Sending"), {
                'fields' : [('created_by', 'handled_by', 'send', 'dispatched')]
                }),
        ]

    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.handled_by = request.user
        obj.save()

    def queryset(self, request):
        # Filter out mass communications which are already dispatched
        # There is no use in displaying the many repetitive rows that
        # arrise from mass communications once they are dispatched. If
        # however not dispatched yet, these communications
        # still require admin action and should be visible.
        qs = super(CommunicationAdmin, self).queryset(request)
        return qs.exclude(type='mass', dispatched='true')

class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'subject')
    ordering = ('name',)

    def save_form(self, request, form, change):
        super(AutomaticCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        if "_continue" in request.POST and request.POST["_continue"] == "test_mail":
            mailing.send_mass_communication(obj, ["fake_user"], request, False)
        # TODO: Generate some summary info message into request about the result
        return obj

class MassCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'method', 'subject')
    ordering = ('date',)

    filter_horizontal = ('send_to_users',)
    
    formfield_overrides = {
        django.db.models.CharField: {'widget': django.forms.TextInput(attrs={'size':'60'})},
    }
    
    fieldsets = [
        (_("Basic"), {
                'fields' : [('name', 'method', 'date', 'note')]
                }),
        (_("Content"), {
                'fields': [('subject', 'subject_en'),
                           ('template', 'template_en'),
                           ('attachment', 'attach_tax_confirmation')]
                }),
        (_("Sending"), {
                'fields' : ['send_to_users']
                }),
        ]

    def save_form(self, request, form, change):
        super(MassCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        if "_continue" in request.POST and request.POST["_continue"] == "test_mail":
            mailing.send_mass_communication(obj, ["fake_user"], request, False)

        if "_continue" in request.POST and request.POST["_continue"] == "send_mails":
            mailing.send_mass_communication(obj, obj.send_to_users.all(), request)
            # Sending was done, so revert the state of the 'send' checkbox back to False
            obj.date = datetime.datetime.now()
            obj.save()
        # TODO: Generate some summary info message into request about the result
        return obj

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('conds',)
    fieldsets = [
        (_("Description"), {
                'fields' : ['name']
                }),
        (_("Operator"), {
                'fields' : ['operation']
                }),
        (_("Comparing conditions operands"), {
                'fields': [('variable', 'value')]
                }),
        (_("Logical conditions operands"), {
                'fields': ['conds']
                }),
        (_("Usage"), {
                'fields': ['as_filter']
                }),
        ]

    ordering = ('name',)

class AccountStatementsAdmin(admin.ModelAdmin):
    list_display = ('import_date', 'csv_file', 'date_from', 'date_to')
    inlines = [PaymentsInlineNoExtra]
    readonly_fields = ('import_date', 'date_from', 'date_to')
    fields = copy.copy(list_display)

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('created', 'name', 'number_of_members', 'number_of_recruiters', 'total_expenses')
    fields = ('created', 'name')
    inlines = (ExpenseInline, )

class RecruiterAdmin(admin.ModelAdmin):
    list_display = ('recruiter_id', 'person_name', 'email', 'telephone', 'problem', 'rating')
    list_filter = ('problem',)
    actions = (export_as_csv_action(fields=list(list_display)+['note']),)
    filter_horizontal = ('campaigns',)

class TaxConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'amount', 'file')
    ordering = ('user__surname', 'user__firstname',)
    list_filter = ['year',]
    search_fields = ('user__surname', 'user__firstname', 'user__variable_symbol',)
    actions = (export_as_csv_action(fields=('user', 'amount')),)

    def generate(self, request):
	year = 2012
	payed = Payment.objects.filter(date__year=year).exclude(type='expected').values_list('user_id', flat=True)
	donors = User.objects.filter(id__in=payed).order_by('surname')
	count = 0
	for d in donors:
	    c = d.make_tax_confirmation(year)
	    if c:
		count += 1
        messages.info(request, 'Generated %d tax confirmations' % count)
	return HttpResponseRedirect(reverse('admin:aklub_taxconfirmation_changelist'))

    def get_urls(self):
        from django.conf.urls import patterns, url
        urls = super(TaxConfirmationAdmin, self).get_urls()
        my_urls = patterns('',
            url(
                r'generate',
                self.admin_site.admin_view(self.generate),
                name='aklub_taxconfirmation_generate',
            ),
        )
        return my_urls + urls
    

admin.site.register(User, UserAdmin)
admin.site.register(NewUser, NewUserAdmin)
admin.site.register(Communication, CommunicationAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(MassCommunication, MassCommunicationAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(Campaign, CampaignAdmin)
admin.site.register(Recruiter, RecruiterAdmin)
admin.site.register(TaxConfirmation, TaxConfirmationAdmin)
