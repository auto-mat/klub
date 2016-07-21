# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0014_auto_20150929_1328'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_payment_date',
        ),
        migrations.AddField(
            model_name='user',
            name='last_payment',
            field=models.ForeignKey(related_name='user_last_payment', default=None, editable=False, null=True, to='aklub.Payment'),
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='value',
            field=models.CharField(help_text='Value or variable on right-hand side. <br/>\naction: daily, new-user<br/>\nDateField: month_ago, one_day, one_week, two_weeks, one_month<br/>\nBooleanField: True, False', max_length=50, null=True, verbose_name='Value', blank=True),
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='variable',
            field=models.CharField(choices=[(b'User.active', 'User Active: BooleanField '), (b'User.activity_points', 'User Activity points: IntegerField '), (b'User.additional_information', 'User Additional information: TextField '), (b'User.addressment', 'User Addressment in letter: CharField '), (b'User.addressment_on_envelope', 'User Addressment on envelope: CharField '), (b'User.city', 'User City/City part: CharField '), (b'User.club_card_available', 'User Club card available: BooleanField '), (b'User.club_card_dispatched', 'User Club card dispatched?: BooleanField '), (b'User.country', 'User Country: CharField '), (b'User.different_correspondence_address', 'User Different correspondence address: BooleanField '), (b'User.email', 'User Email: CharField '), (b'User.exceptional_membership', 'User Exceptional membership: BooleanField '), (b'User.expected_date_of_first_payment', 'User Expected date of first payment: DateField '), (b'User.expected_regular_payment_date', 'User expected regular payment date: DateField '), (b'User.extra_money', 'User extra money: IntegerField '), (b'User.field_of_work', 'User Field of work: CharField '), (b'User.firstname', 'User First name: CharField '), ('User.id', 'User ID: AutoField '), (b'User.knows_us_from', 'User Where does he/she know us from?: CharField '), (b'User.language', "User Language: CharField ('cs', 'en')"), (b'User.last_payment', 'User last payment: DenormDBField '), (b'User.no_upgrade', 'User no upgrade: NullBooleanField '), (b'User.note', 'User Note for making a boring form more lively: TextField '), (b'User.number_of_payments', 'User number of payments: IntegerField '), (b'User.old_account', 'User Old account: BooleanField '), (b'User.other_benefits', 'User Other benefits: TextField '), (b'User.other_support', 'User Other support: TextField '), (b'User.payment_total', 'User payment total: FloatField '), (b'User.profile_picture', 'User Profile picture: FileField '), (b'User.profile_text', 'User What is your reason?: TextField '), (b'User.public', 'User Publish my name in the list of supporters: BooleanField '), (b'User.recruiter', 'User recruiter: ForeignKey '), (b'User.registered_support', 'User Registered support: DateTimeField '), (b'User.regular_amount', 'User Regularly (amount): PositiveIntegerField '), (b'User.regular_frequency', "User Frequency of regular payments: CharField ('monthly', 'quaterly', 'biannually', 'annually')"), (b'User.regular_payments', 'User Regular payments: BooleanField '), (b'User.sex', "User Gender: CharField ('male', 'female', 'unknown')"), (b'User.source', 'User Source: ForeignKey '), (b'User.street', 'User Street and number: CharField '), (b'User.surname', 'User Surname: CharField '), (b'User.telephone', 'User Telephone: CharField '), (b'User.title_after', 'User Title after name: CharField '), (b'User.title_before', 'User Title before name: CharField '), (b'User.variable_symbol', 'User Variable symbol: CharField '), (b'User.verified', 'User Verified: BooleanField '), (b'User.verified_by', 'User Verified by: ForeignKey '), (b'User.why_supports', 'User Why does he/she support us?: TextField '), (b'User.wished_information', 'User Send regular news via email: BooleanField '), (b'User.wished_tax_confirmation', 'User Send tax confirmation: BooleanField '), (b'User.wished_welcome_letter', 'User Send welcome letter: BooleanField '), (b'User.zip_code', 'User ZIP Code: CharField '), (b'User.last_payment.BIC', 'User.last_payment BIC: CharField '), (b'User.last_payment.KS', 'User.last_payment CS: CharField '), (b'User.last_payment.SS', 'User.last_payment SS: CharField '), (b'User.last_payment.VS', 'User.last_payment VS: CharField '), (b'User.last_payment.account', 'User.last_payment Account: CharField '), (b'User.last_payment.account_name', 'User.last_payment Account name: CharField '), (b'User.last_payment.account_statement', 'User.last_payment account statement: ForeignKey '), (b'User.last_payment.amount', 'User.last_payment Amount: PositiveIntegerField '), (b'User.last_payment.bank_code', 'User.last_payment Bank code: CharField '), (b'User.last_payment.bank_name', 'User.last_payment Bank name: CharField '), (b'User.last_payment.date', 'User.last_payment Date of payment: DateField '), (b'User.last_payment.done_by', 'User.last_payment Done by: CharField '), ('User.last_payment.id', 'User.last_payment ID: AutoField '), (b'User.last_payment.type', "User.last_payment Type: CharField ('bank-transfer', 'cash', 'expected', 'darujme')"), (b'User.last_payment.user', 'User.last_payment user: ForeignKey '), (b'User.last_payment.user_identification', 'User.last_payment Sender identification: CharField '), (b'User.source.direct_dialogue', 'User.source Is from Direct Dialogue: BooleanField '), ('User.source.id', 'User.source ID: AutoField '), (b'User.source.name', 'User.source Name: CharField '), (b'User.source.slug', 'User.source Slug: SlugField '), (b'action', "Action: CharField ('daily', 'new-user', 'new-payment')")], max_length=50, blank=True, help_text='Value or variable on left-hand side', null=True, verbose_name='Variable'),
        ),
    ]
