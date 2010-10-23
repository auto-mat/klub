from django.contrib import admin

from aklub.models import User, Payment, Communication, AutomaticCommunication, Condition, AccountStatements, UserImports 

class PaymentsInline(admin.TabularInline):
    model = Payment
    list_display = ('amount', 'person_name', 'date', 'paired_with_expected')
    ordering = ('date',)
    extra = 5

class CommunicationInline(admin.TabularInline):
    model = Communication
    extra = 1
    ordering = ('date',)

class UserAdmin(admin.ModelAdmin):
    list_display = ('surname', 'person_name', 'variable_symbol', 'regular_payments', 'registered_support', 
                    'payments', 'total_contrib', 'monthly_payment', 'requires_action')
    list_filter = ['regular_payments', 'language']
    search_fields = ['firstname', 'surname']

    ordering = ('-surname',)

    save_as = True

    inlines = [PaymentsInline, CommunicationInline]

    fieldsets = [
        ('Basic personal', {
                'fields': ['firstname', 'surname',  'sex', 'language']}),
        ('Titles and addressments', {
                'fields': ['title_before', 'title_after', 'addressment',
                           'addressment_on_envelope',],
                'classes': ['collapse']}),
        ('Contacts', {'fields': ['email', 'telephone', 'street',
                                 'city', 'country', 'zip_code'],
                      'classes': ['collapse']}),
        ('Additional', {'fields': ['age', 'knows_us_from',  'why_supports', 'field_of_work',
                                   'source', 'additional_information'],
                        'classes': ['collapse']}),
        ('Support', {'fields': ['variable_symbol',
                                'registered_support', 'exceptional_membership', 'regular_payments',
                                'other_support', 'monthly_payment']}),
        ('Communication', {'fields': ['wished_information'],
                           'classes': ['collapse']}),
        ('Benefits', {'fields': ['club_card_available', 'club_card_dispatched', 'other_benefits'],
                      'classes': ['collapse']}),
        ('Note', {'fields': ['note',],
                  'classes': ['collapse']}),
        ]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'amount', 'person_name', 'account', 'bank_code', 'VS', 'user_identification', 'type', 'done_by', 'paired_with_expected')
    raw_id_fields = ('user',)
    ordering = ('date',)
    list_filter = ['user',]
    search_fields = ['person_name', 'user', 'amount', 'VS']


class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'dispatched', 'user', 'method', 'handled_by', 'date')
    raw_id_fields = ('user',)
    ordering = ('-date',)
    list_filter = ['dispatched']

class AutomaticCommunicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'condition', 'method', 'subject')
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


admin.site.register(Communication, CommunicationAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(AccountStatements, AccountStatementsAdmin)
admin.site.register(UserImports, UserImportsAdmin)
admin.site.register(AutomaticCommunication, AutomaticCommunicationAdmin)
admin.site.register(Condition, ConditionAdmin)
