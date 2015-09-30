# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0015_auto_20150929_1526'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='regular_payments_delay',
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='variable',
            field=models.CharField(choices=[(b'User.active', 'User Active: BooleanField '), (b'User.activity_points', 'User Activity points: IntegerField '), (b'User.additional_information', 'User Additional information: TextField '), (b'User.addressment', 'User Addressment in letter: CharField '), (b'User.addressment_on_envelope', 'User Addressment on envelope: CharField '), (b'User.city', 'User City/City part: CharField '), (b'User.club_card_available', 'User Club card available: BooleanField '), (b'User.club_card_dispatched', 'User Club card dispatched?: BooleanField '), (b'User.country', 'User Country: CharField '), (b'User.different_correspondence_address', 'User Different correspondence address: BooleanField '), (b'User.email', 'User Email: CharField '), (b'User.exceptional_membership', 'User Exceptional membership: BooleanField '), (b'User.expected_date_of_first_payment', 'User Expected date of first payment: DateField '), (b'User.expected_regular_payment_date', 'User expected regular payment date: DateField '), (b'User.extra_money', 'User extra money: IntegerField '), (b'User.field_of_work', 'User Field of work: CharField '), (b'User.firstname', 'User First name: CharField '), ('User.id', 'User ID: AutoField '), (b'User.knows_us_from', 'User Where does he/she know us from?: CharField '), (b'User.language', "User Language: CharField ('cs', 'en')"), (b'User.last_payment_date', 'User last payment date: DateField '), (b'User.last_payment_type', 'User last payment type: CharField '), (b'User.no_upgrade', 'User no upgrade: NullBooleanField '), (b'User.note', 'User Note for making a boring form more lively: TextField '), (b'User.number_of_payments', 'User number of payments: IntegerField '), (b'User.old_account', 'User Old account: BooleanField '), (b'User.other_benefits', 'User Other benefits: TextField '), (b'User.other_support', 'User Other support: TextField '), (b'User.payment_total', 'User payment total: FloatField '), (b'User.profile_picture', 'User Profile picture: FileField '), (b'User.profile_text', 'User What is your reason?: TextField '), (b'User.public', 'User Publish my name in the list of supporters: BooleanField '), (b'User.recruiter', 'User recruiter: ForeignKey '), (b'User.registered_support', 'User Registered support: DateTimeField '), (b'User.regular_amount', 'User Regularly (amount): PositiveIntegerField '), (b'User.regular_frequency', "User Frequency of regular payments: CharField ('monthly', 'quaterly', 'biannually', 'annually')"), (b'User.regular_payments', 'User Regular payments: BooleanField '), (b'User.sex', "User Gender: CharField ('male', 'female', 'unknown')"), (b'User.source', 'User Source: ForeignKey '), (b'User.street', 'User Street and number: CharField '), (b'User.surname', 'User Surname: CharField '), (b'User.telephone', 'User Telephone: CharField '), (b'User.title_after', 'User Title after name: CharField '), (b'User.title_before', 'User Title before name: CharField '), (b'User.variable_symbol', 'User Variable symbol: CharField '), (b'User.verified', 'User Verified: BooleanField '), (b'User.verified_by', 'User Verified by: ForeignKey '), (b'User.why_supports', 'User Why does he/she support us?: TextField '), (b'User.wished_information', 'User Send regular news via email: BooleanField '), (b'User.wished_tax_confirmation', 'User Send tax confirmation: BooleanField '), (b'User.wished_welcome_letter', 'User Send welcome letter: BooleanField '), (b'User.zip_code', 'User ZIP Code: CharField '), (b'User.source.direct_dialogue', 'User.source Is from Direct Dialogue: BooleanField '), ('User.source.id', 'User.source ID: AutoField '), (b'User.source.name', 'User.source Name: CharField '), (b'User.source.slug', 'User.source Slug: SlugField '), (b'action', "Action: CharField ('daily', 'new-user', 'new-payment')")], max_length=50, blank=True, help_text='Value or variable on left-hand side', null=True, verbose_name='Variable'),
        ),
    ]
