# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0014_auto_20150929_1328'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_payment_type',
            field=models.CharField(max_length=20, null=True, editable=False),
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='variable',
            field=models.CharField(choices=[(b'User.active', 'Active: BooleanField '), (b'User.activity_points', 'Activity points: IntegerField '), (b'User.additional_information', 'Additional information: TextField '), (b'User.addressment', 'Addressment in letter: CharField '), (b'User.addressment_on_envelope', 'Addressment on envelope: CharField '), (b'User.city', 'City/City part: CharField '), (b'User.club_card_available', 'Club card available: BooleanField '), (b'User.club_card_dispatched', 'Club card dispatched?: BooleanField '), (b'User.country', 'Country: CharField '), (b'User.different_correspondence_address', 'Different correspondence address: BooleanField '), (b'User.email', 'Email: CharField '), (b'User.exceptional_membership', 'Exceptional membership: BooleanField '), (b'User.expected_date_of_first_payment', 'Expected date of first payment: DateField '), (b'User.expected_regular_payment_date', 'expected regular payment date: DateField '), (b'User.extra_money', 'extra money: IntegerField '), (b'User.field_of_work', 'Field of work: CharField '), (b'User.firstname', 'First name: CharField '), ('User.id', 'ID: AutoField '), (b'User.knows_us_from', 'Where does he/she know us from?: CharField '), (b'User.language', "Language: CharField ('cs', 'en')"), (b'User.last_payment_date', 'last payment date: DateField '), (b'User.last_payment_type', 'last payment type: CharField '), (b'User.no_upgrade', 'no upgrade: NullBooleanField '), (b'User.note', 'Note for making a boring form more lively: TextField '), (b'User.number_of_payments', 'number of payments: IntegerField '), (b'User.old_account', 'Old account: BooleanField '), (b'User.other_benefits', 'Other benefits: TextField '), (b'User.other_support', 'Other support: TextField '), (b'User.payment_total', 'payment total: FloatField '), (b'User.profile_picture', 'Profile picture: FileField '), (b'User.profile_text', 'What is your reason?: TextField '), (b'User.public', 'Publish my name in the list of supporters: BooleanField '), (b'User.recruiter', 'recruiter: ForeignKey '), (b'User.registered_support', 'Registered support: DateTimeField '), (b'User.regular_amount', 'Regularly (amount): PositiveIntegerField '), (b'User.regular_frequency', "Frequency of regular payments: CharField ('monthly', 'quaterly', 'biannually', 'annually')"), (b'User.regular_payments', 'Regular payments: BooleanField '), (b'User.regular_payments_delay', 'regular payments delay: DenormDBField '), (b'User.sex', "Gender: CharField ('male', 'female', 'unknown')"), (b'User.source', 'Source: ForeignKey '), (b'User.street', 'Street and number: CharField '), (b'User.surname', 'Surname: CharField '), (b'User.telephone', 'Telephone: CharField '), (b'User.title_after', 'Title after name: CharField '), (b'User.title_before', 'Title before name: CharField '), (b'User.variable_symbol', 'Variable symbol: CharField '), (b'User.verified', 'Verified: BooleanField '), (b'User.verified_by', 'Verified by: ForeignKey '), (b'User.why_supports', 'Why does he/she support us?: TextField '), (b'User.wished_information', 'Send regular news via email: BooleanField '), (b'User.wished_tax_confirmation', 'Send tax confirmation: BooleanField '), (b'User.wished_welcome_letter', 'Send welcome letter: BooleanField '), (b'User.zip_code', 'ZIP Code: CharField '), (b'action', "Action: CharField ('daily', 'new-user', 'new-payment')")], max_length=50, blank=True, help_text='Value or variable on left-hand side', null=True, verbose_name='Variable'),
        ),
    ]
