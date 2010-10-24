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

# Django imports
from django.contrib import admin
from django.utils.translation import ugettext as _
# Local models
from aklub.models import User, Payment, Communication, AutomaticCommunication, \
    Condition, AccountStatements, UserImports 

# -- INLINE FORMS --
class PaymentsInline(admin.TabularInline):
    model = Payment
    list_display = ('amount', 'person_name', 'date', 'paired_with_expected')
    ordering = ('date',)
    extra = 5

class CommunicationInline(admin.TabularInline):
    model = Communication
    extra = 1
    ordering = ('date',)

# -- ADMIN FORMS --
class UserAdmin(admin.ModelAdmin):
    list_display = ('surname', 'person_name', 'variable_symbol',
                    'regular_payments', 'registered_support', 
                    'payments', 'total_contrib', 'monthly_payment',
                    'requires_action')
    list_filter = ['regular_payments', 'language']
    search_fields = ['firstname', 'surname']
    ordering = ('-surname',)
    save_as = True
    inlines = [PaymentsInline, CommunicationInline]
    fieldsets = [
        ('Basic personal', {
                'fields': [('firstname', 'surname'),
                           ('sex', 'language')]}),
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
                           ('regular_payments', 'monthly_payment',
                            'exceptional_membership'),
                           'other_support']}),
        ('Communication', {
                'fields': ['wished_information'],
                'classes': ['collapse']}),
        ('Benefits', {
                'fields': [('club_card_available', 'club_card_dispatched'),
                           'other_benefits'],
                'classes': ['collapse']}),
        ('Note', {
                'fields': ['note',],
                'classes': ['collapse']}),
        ]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'amount', 'person_name', 'account', 'bank_code',
                    'VS', 'user_identification', 'type', 'paired_with_expected')
    fieldsets = [
        (_("Basic"), {
                'fields' : ['date', 'amount',
                            ('type', )]
                }),
        (_("Details"), {
                'fields': [('account', 'bank_code'),
                           ('account_name', 'bank_name'),
                           ('VS', 'KS', 'SS'),                           
                           'user_identification']
                }),
        ]
    raw_id_fields = ('user',)
    ordering = ('date',)
    list_filter = ['user',]
    search_fields = ['user', 'amount', 'VS']

class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'dispatched', 'user', 'method', 'handled_by',
                    'date')
    raw_id_fields = ('user',)
    ordering = ('-date',)
    list_filter = ['dispatched']

class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'method', 'subject')
    ordering = ('name',)

class ConditionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)

class AccountStatementsAdmin(admin.ModelAdmin):
    list_display = ('import_date', 'csv_file')
    ordering = ('import_date',)

class UserImportsAdmin(admin.ModelAdmin):
    list_display = ('import_date', 'csv_file')
    ordering = ('import_date',)


admin.site.register(User, UserAdmin)
admin.site.register(Communication, CommunicationAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(UserImports, UserImportsAdmin)
