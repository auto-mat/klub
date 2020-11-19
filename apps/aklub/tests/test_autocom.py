# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
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

import datetime

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from interactions.models import Interaction

from model_mommy import mommy

from .. import autocom


class AutocomTest(TestCase):
    """
    testing some types of AutomaticCommunication that is used in views or run as cron job
    all together to check if some bad things happen
    """
    def setUp(self):
        inter_category = mommy.make('interactions.interactioncategory', category='emails')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, send_email=True)
        self.unit = mommy.make('aklub.administrativeunit', name='test_unit')

        self.event = mommy.make('aklub.event', name='test_event', administrative_units=[self.unit, ])
        self.money_account = mommy.make('aklub.BankAccount', bank_account_number=3, administrative_unit=self.unit)

        self.user = mommy.make('aklub.userprofile', administrative_units=[self.unit, ])
        self.channel = mommy.make(
            'aklub.donorpaymentchannel',
            event=self.event,
            money_account=self.money_account,
            user=self.user,
            regular_frequency='monthly',
            regular_payments='regular',
        )
        mommy.make('aklub.ProfileEmail', email='supa_tester@super.com', user=self.user, is_primary=True)

        # first payment communication
        first_payment = mommy.make('flexible_filter_conditions.NamedCondition', name="first_payment")
        condition = mommy.make('flexible_filter_conditions.Condition', operation="and", negate=False, named_condition=first_payment)
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.userchannels.number_of_payments",
            operation="=",
            value="1",
            condition=condition,
        )
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.userchannels.event",
            operation="=",
            value=self.event.id,
            condition=condition,
        )

        self.auto_first_payment = mommy.make(
            "aklub.AutomaticCommunication",
            method_type=inter_type,
            condition=first_payment,
            event=self.event,
            template='This is Template',
            subject='Thanks for first payment',
            only_once=True,
            dispatch_auto=True,
            administrative_unit=self.unit,
        )

        # sign petition communication
        sign_petition = mommy.make('flexible_filter_conditions.NamedCondition', name="sign-petition")
        condition = mommy.make('flexible_filter_conditions.Condition', operation="and", negate=False, named_condition=sign_petition)
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="action",
            operation="=",
            value="user-signature",
            condition=condition,
        )
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.petitionsignature.event",
            operation="=",
            value=self.event.id,
            condition=condition,
        )

        self.auto_sign_petition = mommy.make(
            "aklub.AutomaticCommunication",
            method_type=inter_type,
            condition=sign_petition,
            event=self.event,
            template='Petition-signature',
            subject='Thanks for the signature!',
            only_once=True,
            dispatch_auto=True,
            administrative_unit=self.unit,
        )

        # payment reminder
        payment_reminder = mommy.make('flexible_filter_conditions.NamedCondition', name="payment-remind")
        condition = mommy.make('flexible_filter_conditions.Condition', operation="and", negate=False, named_condition=payment_reminder)
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.userchannels.last_payment.date",
            operation="=",
            value="days_ago.45",
            condition=condition,
        )
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.userchannels.event",
            operation="=",
            value=self.event.id,
            condition=condition,
        )
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.userchannels.regular_frequency",
            operation="=",
            value='monthly',
            condition=condition,
        )
        mommy.make(
            'flexible_filter_conditions.TerminalCondition',
            variable="User.userchannels.regular_payments",
            operation="=",
            value='regular',
            condition=condition,
        )

        self.auto_payment_reminder = mommy.make(
            "aklub.AutomaticCommunication",
            method_type=inter_type,
            condition=payment_reminder,
            event=self.event,
            template='Did you pay?',
            subject='Well, okey',
            only_once=False,
            dispatch_auto=True,
            administrative_unit=self.unit,
        )
        """
        AutomaticCommunication.objects.create(
            method_type=inter_type,
            condition=nc,
            event=self.event,
            template="Vazen{y|a} {pane|pani} $addressment $regular_frequency testovací šablona",
            template_en="Dear {sir|miss} $addressment $regular_frequency test template",
            subject="Testovací komunikace",
            subject_en="Testing interaction",
            administrative_unit=unit,
        )
        """
    def test_autocom_first_payment(self):
        """
        send autocom when first payment is paired with donor payment channel (cron-autocom)
        """
        mommy.make('aklub.payment', recipient_account=self.money_account, amount=1212, user_donor_payment_channel=self.channel)
        autocom.check()
        interactions = self.user.interaction_set.all()
        self.assertEqual(interactions.count(), 1)
        inter = interactions.first()
        self.assertEqual(inter.subject, self.auto_first_payment.subject)
        self.assertEqual(inter.summary, self.auto_first_payment.template)
        self.assertEqual(inter.dispatched, True)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, self.auto_first_payment.subject)
        self.assertEqual(email.body, self.auto_first_payment.template)

        self.auto_first_payment.refresh_from_db()
        self.assertTrue(self.user in self.auto_first_payment.sent_to_users.all())

    def test_autocom_sign_petition(self):
        """
        check autocom =>  petition signing  (action-autocom)
        """
        mommy.make('interactions.PetitionSignature', user=self.user, administrative_unit=self.unit, event=self.event)
        autocom.check(action='user-signature')
        interactions = self.user.interaction_set.all()
        self.assertEqual(interactions.count(), 1)
        inter = interactions.first()
        self.assertEqual(inter.subject, self.auto_sign_petition.subject)
        self.assertEqual(inter.summary, self.auto_sign_petition.template)
        self.assertEqual(inter.dispatched, True)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, self.auto_sign_petition.subject)
        self.assertEqual(email.body, self.auto_sign_petition.template)

        self.auto_first_payment.refresh_from_db()
        self.assertTrue(self.user in self.auto_sign_petition.sent_to_users.all())

    def test_autocom_monthly_payment_delay(self):
        """
        payment was not received => regular donor (cron-autocom)
        can be called multiple times
        """
        date = timezone.now().date() - datetime.timedelta(days=45)
        mommy.make(
            'aklub.payment',
            recipient_account=self.money_account,
            amount=1,
            user_donor_payment_channel=self.channel,
            date='1994-11-11',
        )
        mommy.make(
            'aklub.payment',
            recipient_account=self.money_account,
            amount=1,
            user_donor_payment_channel=self.channel,
            date=date,
        )

        autocom.check()

        interactions = self.user.interaction_set.all()
        self.assertEqual(interactions.count(), 1)
        inter = interactions.first()
        self.assertEqual(inter.subject, self.auto_payment_reminder.subject)
        self.assertEqual(inter.summary, self.auto_payment_reminder.template)
        self.assertEqual(inter.dispatched, True)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, self.auto_payment_reminder.subject)
        self.assertEqual(email.body, self.auto_payment_reminder.template)

        # can be really send multiple times?
        autocom.check()
        interactions = self.user.interaction_set.all()
        self.assertEqual(interactions.count(), 2)
        self.assertEqual(len(mail.outbox), 2)


class AutocomAddressmentTest(TestCase):
    def setUp(self):
        self.userprofile = mommy.make('aklub.userprofile', sex='male')
        self.event = mommy.make('aklub.event')
        self.au = mommy.make('aklub.administrativeunit', name='test')
        self.bankacc = mommy.make('aklub.BankAccount', bank_account_number=11111, administrative_unit=self.au)
        self.payment_channel = mommy.make('aklub.DonorPaymentChannel', user=self.userprofile, event=self.event, money_account=self.bankacc)
        named_condition = mommy.make('flexible_filter_conditions.NamedCondition')
        condition = mommy.make('flexible_filter_conditions.Condition', operation="or", negate=True, named_condition=named_condition)
        mommy.make(
            "flexible_filter_conditions.TerminalCondition",
            variable="action",
            value="test-autocomm",
            operation="==",
            condition=condition,
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        unit = mommy.make('aklub.administrativeunit', name='testAU')

        mommy.make(
            "aklub.AutomaticCommunication",
            method_type=inter_type,
            condition=named_condition,
            template="Vazen{y|a} {pane|pani} $addressment $regular_frequency testovací šablona",
            template_en="Dear {sir|miss} $addressment $regular_frequency test template",
            subject="Testovací komunikace",
            subject_en="Testing interaction",
            administrative_unit=unit,
        )

    def test_autocom(self):
        autocom.check(action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertTrue("testovací šablona" in interaction.summary)
        self.assertTrue("příteli Auto*Matu" in interaction.summary)
        self.assertTrue("Vazeny pane" in interaction.summary)

    def test_autocom_female(self):
        self.userprofile.sex = 'female'
        self.userprofile.save()
        autocom.check(action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("testovací šablona", interaction.summary)
        self.assertIn("přítelkyně Auto*Matu", interaction.summary)
        self.assertIn("Vazena pani", interaction.summary)

    def test_autocom_unknown(self):
        self.userprofile.sex = 'unknown'
        self.userprofile.save()
        autocom.check(action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("testovací šablona", interaction.summary)
        self.assertIn("příteli/kyně Auto*Matu", interaction.summary)
        self.assertIn("Vazeny/a pane/pani", interaction.summary)

    def test_autocom_addressment(self):
        self.userprofile.sex = 'male'
        self.userprofile.addressment = 'own addressment'
        self.userprofile.save()
        autocom.check(action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("testovací šablona", interaction.summary)
        self.assertIn("own addressment", interaction.summary)
        self.assertIn("Vazeny pane", interaction.summary)

    def test_autocom_en(self):
        self.userprofile.sex = 'unknown'
        self.userprofile.language = 'en'
        self.userprofile.save()
        autocom.check(action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("test template", interaction.summary)
        self.assertIn("Auto*Mat friend", interaction.summary)
        self.assertIn("Dear sir", interaction.summary)


class GenderStringsValidatorTest(TestCase):
    def test_matches(self):
        self.assertEquals(autocom.gendrify_text('', 'male'), '')
        self.assertEquals(autocom.gendrify_text('asdfasdf', 'male'), 'asdfasdf')
        self.assertEquals(autocom.gendrify_text('{ý|á}', 'male'), 'ý')
        self.assertEquals(autocom.gendrify_text('{ý|á}', 'female'), 'á')
        self.assertEquals(autocom.gendrify_text('{ý/á}', 'female'), 'á')
        self.assertEquals(autocom.gendrify_text('{|á}', 'male'), '')
        self.assertEquals(autocom.gendrify_text('{|á}', 'female'), 'á')
        self.assertEquals(autocom.gendrify_text('{|á}', ''), '/á')
        self.assertEquals(autocom.gendrify_text('asdfasdf{ý|á}', 'male'), 'asdfasdfý')
        self.assertEquals(autocom.gendrify_text('{ý|á}asdfadsfasd', 'male'), 'ýasdfadsfasd')
        self.assertEquals(autocom.gendrify_text('asdfasdf{ý|á}asdfadsfasd', ''), 'asdfasdfý/áasdfadsfasd')
        self.assertEquals(autocom.gendrify_text('asdfasdf{ý/á}asdfadsfasd', ''), 'asdfasdfý/áasdfadsfasd')
        self.assertEquals(autocom.gendrify_text('{ý|á}{ý|á}', 'male'), 'ýý')
        self.assertEquals(autocom.gendrify_text('{ý|á}asdfasdf{ý|á}', 'male'), 'ýasdfasdfý')
        self.assertEquals(autocom.gendrify_text('{ý/á}asdfasdf{ý|á}', 'male'), 'ýasdfasdfý')

    def test_mismatches(self):
        with self.assertRaises(ValidationError):
            autocom.gendrify_text('{ý.á}', 'male')
        with self.assertRaises(ValidationError):
            autocom.gendrify_text('{ý|á}{ý.á}', 'male')
        with self.assertRaises(ValidationError):
            autocom.gendrify_text('{ý.á}{ý|á}', 'male')
        with self.assertRaises(ValidationError):
            autocom.gendrify_text('{ý.á}asdfasdfasdf', 'male')
        with self.assertRaises(ValidationError):
            autocom.gendrify_text('asdfasdfasdf{ý.á}', 'male')
        with self.assertRaises(ValidationError):
            autocom.gendrify_text('asdfasfasfaiasdfasfasdfsdfsfasdfasfasfasfasdfasd{ý.á}')
