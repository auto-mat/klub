# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0005_auto_20150730_1424'),
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(help_text='Identifier of the source', max_length=100, verbose_name='Slug')),
                ('name', models.CharField(help_text='Name of the source', max_length=100, verbose_name='Name')),
                ('direct_dialogue', models.BooleanField(default=False, verbose_name='Is from Direct Dialogue')),
            ],
            options={
                'verbose_name': 'Source',
                'verbose_name_plural': 'Sources',
            },
        ),
        migrations.AlterField(
            model_name='automaticcommunication',
            name='sent_to_users',
            field=models.ManyToManyField(help_text='List of users to whom this communication was already sent', to='aklub.User', editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='condition',
            name='value',
            field=models.CharField(help_text='Value or variable on right-hand side', max_length=50, null=True, verbose_name='Value', blank=True),
        ),
        migrations.AlterField(
            model_name='condition',
            name='variable',
            field=models.CharField(choices=[(b'User.DoesNotExist', 'DoesNotExist: function '), (b'User.MultipleObjectsReturned', 'MultipleObjectsReturned: function '), (b'User.active', 'Active: BooleanField '), (b'User.activity_points', 'Activity points: IntegerField '), (b'User.additional_information', 'Additional information: TextField '), (b'User.addressment', 'Addressment in letter: CharField '), (b'User.addressment_on_envelope', 'Addressment on envelope: CharField '), (b'User.city', 'City/City part: CharField '), (b'User.club_card_available', 'Club card available: BooleanField '), (b'User.club_card_dispatched', 'Club card dispatched?: BooleanField '), (b'User.country', 'Country: CharField '), (b'User.different_correspondence_address', 'Different correspondence address: BooleanField '), (b'User.email', 'Email: CharField '), (b'User.exceptional_membership', 'Exceptional membership: BooleanField '), (b'User.expected_date_of_first_payment', 'Expected date of first payment: DateField '), (b'User.expected_regular_payment_date', 'expected_regular_payment_date: function '), (b'User.extra_money', 'extra_money: Integer '), (b'User.extra_payments', 'Extra money: function '), (b'User.field_of_work', 'Field of work: CharField '), (b'User.firstname', 'First name: CharField '), (b'User.get_language_display', 'get_language_display: function '), (b'User.get_next_by_registered_support', 'get_next_by_registered_support: function '), (b'User.get_previous_by_registered_support', 'get_previous_by_registered_support: function '), (b'User.get_regular_frequency_display', 'get_regular_frequency_display: function '), (b'User.get_sex_display', 'get_sex_display: function '), (b'User.get_source_display', 'get_source_display: function '), ('User.id', 'ID: AutoField '), (b'User.is_direct_dialogue', 'is_direct_dialogue: function '), (b'User.knows_us_from', 'Where does he/she know us from?: CharField '), (b'User.language', "Language: CharField ('cs', 'en')"), (b'User.last_payment', 'last_payment: function '), (b'User.last_payment_date', 'Last payment: Date '), (b'User.mail_communications_count', 'mail_communications_count: function '), (b'User.make_tax_confirmation', 'make_tax_confirmation: function '), (b'User.monthly_regular_amount', 'monthly_regular_amount: function '), (b'User.no_upgrade', 'no_upgrade: Boolean '), (b'User.note', 'Note for making a boring form more lively: TextField '), (b'User.number_of_payments', '# payments: Integer '), (b'User.old_account', 'Old account: BooleanField '), (b'User.other_benefits', 'Other benefits: TextField '), (b'User.other_support', 'Other support: TextField '), (b'User.payment_delay', 'Payment delay: function '), (b'User.payments', 'payments: function '), (b'User.person_name', 'Full name: function '), (b'User.profile_picture', 'Profile picture: FileField '), (b'User.profile_text', 'What is your reason?: TextField '), (b'User.public', 'Publish my name in the list of supporters: BooleanField '), (b'User.recruiter', 'recruiter: ForeignKey '), (b'User.registered_support', 'Registered support: DateTimeField '), (b'User.registered_support_date', 'Registration: function '), (b'User.regular_amount', 'Regularly (amount): PositiveIntegerField '), (b'User.regular_frequency', "Frequency of regular payments: CharField ('monthly', 'quaterly', 'biannually', 'annually')"), (b'User.regular_frequency_td', 'regular_frequency_td: function '), (b'User.regular_payments', 'Regular payments: BooleanField '), (b'User.regular_payments_delay', 'regular_payments_delay: TimeDelta '), (b'User.regular_payments_info', 'Expected payment: function '), (b'User.requires_action', 'requires_action: function '), (b'User.sex', "Gender: CharField ('male', 'female', 'unknown')"), (b'User.source', "Source: CharField ('web', 'dpnk', 'lead-dpnk', 'direct-dialogue-partial-form', 'direct-dialogue-full-form', 'telephone-call', 'personal', 'darujme', 'other')"), (b'User.source_foreign', 'Source: ForeignKey '), (b'User.street', 'Street and number: CharField '), (b'User.surname', 'Surname: CharField '), (b'User.telephone', 'Telephone: CharField '), (b'User.title_after', 'Title after name: CharField '), (b'User.title_before', 'Title before name: CharField '), (b'User.total_contrib', 'Total: Integer '), (b'User.total_contrib_string', 'Total: Integer '), (b'User.variable_symbol', 'Variable symbol: CharField '), (b'User.verified', 'Verified: BooleanField '), (b'User.verified_by', 'Verified by: ForeignKey '), (b'User.why_supports', 'Why does he/she support us?: TextField '), (b'User.wished_information', 'Send regular news via email: BooleanField '), (b'User.wished_tax_confirmation', 'Send tax confirmation: BooleanField '), (b'User.wished_welcome_letter', 'Send welcome letter: BooleanField '), (b'User.zip_code', 'ZIP Code: CharField '), (b'User.last_payment.BIC', 'BIC: CharField '), (b'User.last_payment.DoesNotExist', 'DoesNotExist: function '), (b'User.last_payment.KS', 'CS: CharField '), (b'User.last_payment.MultipleObjectsReturned', 'MultipleObjectsReturned: function '), (b'User.last_payment.SS', 'SS: CharField '), (b'User.last_payment.VS', 'VS: CharField '), (b'User.last_payment.account', 'Account: CharField '), (b'User.last_payment.account_name', 'Account name: CharField '), (b'User.last_payment.account_statement', 'account statement: ForeignKey '), (b'User.last_payment.amount', 'Amount: PositiveIntegerField '), (b'User.last_payment.bank_code', 'Bank code: CharField '), (b'User.last_payment.bank_name', 'Bank name: CharField '), (b'User.last_payment.date', 'Date of payment: DateField '), (b'User.last_payment.done_by', 'Done by: CharField '), (b'User.last_payment.get_next_by_date', 'get_next_by_date: function '), (b'User.last_payment.get_previous_by_date', 'get_previous_by_date: function '), (b'User.last_payment.get_type_display', 'get_type_display: function '), ('User.last_payment.id', 'ID: AutoField '), (b'User.last_payment.paired_with_expected', 'paired_with_expected: function '), (b'User.last_payment.person_name', 'person_name: function '), (b'User.last_payment.type', "Type: CharField ('bank-transfer', 'cash', 'expected', 'darujme')"), (b'User.last_payment.user', 'user: ForeignKey '), (b'User.last_payment.user_identification', 'Sender identification: CharField '), (b'action', "Action: CharField ('daily', 'new-user')")], max_length=50, blank=True, help_text='Value or variable on left-hand side', null=True, verbose_name='Variable'),
        ),
        migrations.AddField(
            model_name='user',
            name='source_foreign',
            field=models.ForeignKey(default=None, to='aklub.Source', max_length=80, blank=True, help_text='How did he contact us / became a member? In direct dialog, please distinguish between partial form (he still needs to send a permanent order into his bank) and full form (we are going to submit his form directly into bank, no further action is needed from him).', null=True, verbose_name='Source', on_delete=models.CASCADE),
        ),
    ]
