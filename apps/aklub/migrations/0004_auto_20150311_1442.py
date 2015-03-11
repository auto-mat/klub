# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0003_auto_20141128_1510'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountstatements',
            name='type',
            field=models.CharField(max_length=20, choices=[(b'account', 'Account statement'), (b'darujme', b'Darujme.cz')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='condition',
            name='variable',
            field=models.CharField(choices=[(b'User.DoesNotExist', b'User.DoesNotExist'), (b'User.GENDER', b'User.GENDER'), (b'User.LANGUAGE', b'User.LANGUAGE'), (b'User.MultipleObjectsReturned', b'User.MultipleObjectsReturned'), (b'User.REGULAR_PAYMENT_FREQUENCIES', b'User.REGULAR_PAYMENT_FREQUENCIES'), (b'User.SOURCE', b'User.SOURCE'), (b'User.active', b'User.active'), (b'User.activity_points', b'User.activity_points'), (b'User.additional_information', b'User.additional_information'), (b'User.addressment', b'User.addressment'), (b'User.addressment_on_envelope', b'User.addressment_on_envelope'), (b'User.annotations', b'User.annotations'), (b'User.campaigns', b'User.campaigns'), (b'User.city', b'User.city'), (b'User.club_card_available', b'User.club_card_available'), (b'User.club_card_dispatched', b'User.club_card_dispatched'), (b'User.communications', b'User.communications'), (b'User.country', b'User.country'), (b'User.different_correspondence_address', b'User.different_correspondence_address'), (b'User.email', b'User.email'), (b'User.exceptional_membership', b'User.exceptional_membership'), (b'User.expected_date_of_first_payment', b'User.expected_date_of_first_payment'), (b'User.expected_regular_payment_date', b'User.expected_regular_payment_date'), (b'User.extra_money', b'User.extra_money'), (b'User.extra_payments', b'User.extra_payments'), (b'User.field_of_work', b'User.field_of_work'), (b'User.firstname', b'User.firstname'), (b'User.get_language_display', b'User.get_language_display'), (b'User.get_next_by_registered_support', b'User.get_next_by_registered_support'), (b'User.get_previous_by_registered_support', b'User.get_previous_by_registered_support'), (b'User.get_regular_frequency_display', b'User.get_regular_frequency_display'), (b'User.get_sex_display', b'User.get_sex_display'), (b'User.get_source_display', b'User.get_source_display'), ('User.id', 'User.id'), (b'User.is_direct_dialogue', b'User.is_direct_dialogue'), (b'User.knows_us_from', b'User.knows_us_from'), (b'User.language', b'User.language'), (b'User.last_payment', b'User.last_payment'), (b'User.last_payment_date', b'User.last_payment_date'), (b'User.mail_communications_count', b'User.mail_communications_count'), (b'User.make_tax_confirmation', b'User.make_tax_confirmation'), (b'User.monthly_regular_amount', b'User.monthly_regular_amount'), (b'User.no_upgrade', b'User.no_upgrade'), (b'User.note', b'User.note'), (b'User.number_of_payments', b'User.number_of_payments'), (b'User.objects', b'User.objects'), (b'User.old_account', b'User.old_account'), (b'User.other_benefits', b'User.other_benefits'), (b'User.other_support', b'User.other_support'), (b'User.payment_delay', b'User.payment_delay'), (b'User.payment_set', b'User.payment_set'), (b'User.payments', b'User.payments'), (b'User.person_name', b'User.person_name'), (b'User.profile_picture', b'User.profile_picture'), (b'User.profile_picture', b'User.profile_picture'), (b'User.profile_text', b'User.profile_text'), (b'User.public', b'User.public'), (b'User.recruiter', b'User.recruiter'), (b'User.recruiter', b'User.recruiter'), (b'User.registered_support', b'User.registered_support'), (b'User.registered_support_date', b'User.registered_support_date'), (b'User.regular_amount', b'User.regular_amount'), (b'User.regular_frequency', b'User.regular_frequency'), (b'User.regular_frequency_td', b'User.regular_frequency_td'), (b'User.regular_payments', b'User.regular_payments'), (b'User.regular_payments_delay', b'User.regular_payments_delay'), (b'User.regular_payments_info', b'User.regular_payments_info'), (b'User.requires_action', b'User.requires_action'), (b'User.sex', b'User.sex'), (b'User.source', b'User.source'), (b'User.street', b'User.street'), (b'User.surname', b'User.surname'), (b'User.telephone', b'User.telephone'), (b'User.title_after', b'User.title_after'), (b'User.title_before', b'User.title_before'), (b'User.total_contrib', b'User.total_contrib'), (b'User.variable_symbol', b'User.variable_symbol'), (b'User.verified', b'User.verified'), (b'User.verified_by', b'User.verified_by'), (b'User.verified_by', b'User.verified_by'), (b'User.why_supports', b'User.why_supports'), (b'User.wished_information', b'User.wished_information'), (b'User.wished_tax_confirmation', b'User.wished_tax_confirmation'), (b'User.wished_welcome_letter', b'User.wished_welcome_letter'), (b'User.zip_code', b'User.zip_code'), (b'User.last_payment.BIC', b'User.last_payment.BIC'), (b'User.last_payment.DoesNotExist', b'User.last_payment.DoesNotExist'), (b'User.last_payment.KS', b'User.last_payment.KS'), (b'User.last_payment.MultipleObjectsReturned', b'User.last_payment.MultipleObjectsReturned'), (b'User.last_payment.SS', b'User.last_payment.SS'), (b'User.last_payment.TYPE_OF_PAYMENT', b'User.last_payment.TYPE_OF_PAYMENT'), (b'User.last_payment.VS', b'User.last_payment.VS'), (b'User.last_payment.account', b'User.last_payment.account'), (b'User.last_payment.account_name', b'User.last_payment.account_name'), (b'User.last_payment.account_statement', b'User.last_payment.account_statement'), (b'User.last_payment.account_statement', b'User.last_payment.account_statement'), (b'User.last_payment.amount', b'User.last_payment.amount'), (b'User.last_payment.bank_code', b'User.last_payment.bank_code'), (b'User.last_payment.bank_name', b'User.last_payment.bank_name'), (b'User.last_payment.date', b'User.last_payment.date'), (b'User.last_payment.done_by', b'User.last_payment.done_by'), (b'User.last_payment.get_next_by_date', b'User.last_payment.get_next_by_date'), (b'User.last_payment.get_previous_by_date', b'User.last_payment.get_previous_by_date'), (b'User.last_payment.get_type_display', b'User.last_payment.get_type_display'), ('User.last_payment.id', 'User.last_payment.id'), (b'User.last_payment.objects', b'User.last_payment.objects'), (b'User.last_payment.paired_with_expected', b'User.last_payment.paired_with_expected'), (b'User.last_payment.person_name', b'User.last_payment.person_name'), (b'User.last_payment.type', b'User.last_payment.type'), (b'User.last_payment.user', b'User.last_payment.user'), (b'User.last_payment.user', b'User.last_payment.user'), (b'User.last_payment.user_identification', b'User.last_payment.user_identification'), (b'action', b'action')], max_length=30, blank=True, help_text='Value or variable on left-hand side', null=True, verbose_name='Variable'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='recruiter',
            name='registered',
            field=models.DateField(default=datetime.datetime(2015, 3, 11, 14, 42, 34, 407562), verbose_name='Registered'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='city',
            field=models.CharField(max_length=40, verbose_name='City/City part', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='registered_support',
            field=models.DateTimeField(default=datetime.datetime(2015, 3, 11, 14, 42, 34, 409424), help_text='When did this user register to support us', verbose_name='Registered support', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='regular_amount',
            field=models.PositiveIntegerField(help_text='Minimum yearly payment is 1800 K\u010d', null=True, verbose_name='Regularly (amount)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='source',
            field=models.CharField(help_text='How did he contact us / became a member? In direct dialog, please distinguish between partial form (he still needs to send a permanent order into his bank) and full form (we are going to submit his form directly into bank, no further action is needed from him).', max_length=80, verbose_name='Source', choices=[(b'web', 'Web form'), (b'dpnk', 'DPNK campaign'), (b'direct-dialogue-partial-form', 'Direct dialogue -- partial form (not automatic in bank)'), (b'direct-dialogue-full-form', 'Direct dialogue -- full form (automatic in bank)'), (b'telephone-call', 'Telephonic call'), (b'personal', 'Personal recommendation'), (b'darujme', b'Darujme.cz'), (b'other', 'Another form of contact')]),
            preserve_default=True,
        ),
    ]
