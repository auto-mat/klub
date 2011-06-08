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
# Django imports
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.contrib.admin.filterspecs import FilterSpec, RelatedFilterSpec
from django.http import HttpResponseRedirect
# Local models
from aklub.models import User, Payment, \
    Communication, AutomaticCommunication, MassCommunication, \
    Condition, AccountStatements, UserImports, Campaign 
from aklub.filters import NullFilterSpec, ConditionFilterSpec

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
    readonly_fields = ('handled_by',)

# -- ADMIN FORMS --
class UserAdmin(admin.ModelAdmin):
    list_display = ('surname', 'person_name', 'active', 'variable_symbol',
                    'regular_payments', 'registered_support', 
                    'number_of_payments', 'total_contrib', 'regular_amount',
                    'requires_action')
    list_filter = ['regular_payments', 'language', 'active', 'firstname']
    search_fields = ['firstname', 'surname']
    ordering = ('surname',)
    actions = ('send_mass_communication',)
    save_as = True
    inlines = [PaymentsInline, CommunicationInline]
    fieldsets = [
        ('Basic personal', {
                'fields': [('firstname', 'surname'),
                           ('sex', 'language', 'active')]}),
        ('Titles and addressments', {
                'fields': [('title_before', 'title_after'),
                           ('addressment', 'addressment_on_envelope')],
                'classes': ['collapse']
                }),
        ('Contacts', {
                'fields': [('email', 'telephone'),
                           ('street', 'city', 'country'),
                           'zip_code'],
                'classes': ['collapse']}),
        ('Additional', {
                'fields': ['age', 'knows_us_from',  'why_supports',
                           'field_of_work', 'source', 'additional_information'],
                'classes': ['collapse']}),
        ('Support', {
                'fields': ['variable_symbol',
                           'registered_support',                           
                           ('regular_payments', 'regular_frequency',
                            'regular_amount', 'exceptional_membership'),
                           'other_support']}),
        ('Communication', {
                'fields': ['wished_information', 'wished_tax_confirmation', 'wished_welcome_letter'],
                'classes': ['collapse']}),
        ('Benefits', {
                'fields': [('club_card_available', 'club_card_dispatched'),
                           'other_benefits'],
                'classes': ['collapse']}),
        ('Note', {
                'fields': ['note', 'campaigns',],
                'classes': ['collapse']}),
        ]

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
                instance.handled_by = request.user
            instance.save()
        formset.save_m2m()

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
    list_filter = ['user', 'date']
    date_hierarchy = 'date'
    search_fields = ['user__surname', 'user__firstname', 'amount', 'VS', 'user_identification']

# Register our custom filter for field 'user' on model 'Payment'
# (Note by HH: I believe this does nothing, see filterspec.py RelatedFilterSpec.insert( etc.
RelatedFilterSpec.register(lambda f,m: bool(f.name=='user' and issubclass(m, Payment)),
                           NullFilterSpec)

class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'dispatched', 'user', 'method', 'handled_by',
                    'date')
    raw_id_fields = ('user',)
    readonly_fields = ('handled_by',)
    list_filter = ['dispatched', 'date', 'method']
    date_hierarchy = 'date'
    ordering = ('-date',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.handled_by = request.user
        obj.save()

class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'subject')
    ordering = ('name',)

class MassCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'subject')
    ordering = ('name',)

    def save_form(self, request, form, change):
        super(MassCommunicationAdmin, self).save_form(request, form, change)
        obj = form.save()
        for user in obj.send_to_users.all():
            c = Communication(user=user, method=obj.method, date=datetime.datetime.now(),
                              subject=obj.subject, summary=obj.template, # TODO: Process template
                              attachment=copy.copy(obj.attachment),
                              note="Prepared by auto*mated mass communications at %s" % datetime.datetime.now(),
                              dispatched=obj.dispatch_auto, handled_by = request.user)
            c.save()
        # TODO: Generate some summary info message into request about the result
        return obj

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('name',)
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

class UserImportsAdmin(admin.ModelAdmin):
    list_display = ('import_date', 'csv_file')

class CampaignAdmin(admin.ModelAdmin):
    list_display = ('created', 'name')


admin.site.register(User, UserAdmin)
admin.site.register(Communication, CommunicationAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(MassCommunication, MassCommunicationAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(UserImports, UserImportsAdmin)
admin.site.register(Campaign, CampaignAdmin)
