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

from django.core.exceptions import ValidationError
from django.test import TestCase

from flexible_filter_conditions.models import Condition, NamedCondition, TerminalCondition

from interactions.models import Interaction

from model_mommy import mommy

from .. import autocom
from ..models import (
                    AdministrativeUnit, AutomaticCommunication, BankAccount, DonorPaymentChannel,
                    Event, UserProfile,
)


class AutocomTest(TestCase):
    def setUp(self):
        self.userprofile = UserProfile.objects.create(sex='male')
        self.event = Event.objects.create(created=datetime.date(2010, 10, 10))
        self.au = AdministrativeUnit.objects.create(name='test')
        self.BankAccount = BankAccount.objects.create(bank_account_number=11111, administrative_unit=self.au)
        self.payment_channel = DonorPaymentChannel.objects.create(user=self.userprofile, event=self.event, money_account=self.BankAccount)
        nc = NamedCondition.objects.create()
        c = Condition.objects.create(operation="nor", named_condition=nc)
        TerminalCondition.objects.create(
            variable="action",
            value="test-autocomm",
            operation="==",
            condition=c,
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        unit = mommy.make('aklub.administrativeunit', name='testAU')
        AutomaticCommunication.objects.create(
            method_type=inter_type,
            condition=nc,
            template="Vazen{y|a} {pane|pani} $addressment $regular_frequency testovací šablona",
            template_en="Dear {sir|miss} $addressment $regular_frequency test template",
            subject="Testovací komunikace",
            subject_en="Testing interaction",
            administrative_unit=unit,
        )

    def test_autocom(self):
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertTrue("testovací šablona" in interaction.summary)
        self.assertTrue("příteli Auto*Matu" in interaction.summary)
        self.assertTrue("Vazeny pane" in interaction.summary)

    def test_autocom_female(self):
        self.userprofile.sex = 'female'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("testovací šablona", interaction.summary)
        self.assertIn("přítelkyně Auto*Matu", interaction.summary)
        self.assertIn("Vazena pani", interaction.summary)

    def test_autocom_unknown(self):
        self.userprofile.sex = 'unknown'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("testovací šablona", interaction.summary)
        self.assertIn("příteli/kyně Auto*Matu", interaction.summary)
        self.assertIn("Vazeny/a pane/pani", interaction.summary)

    def test_autocom_addressment(self):
        self.userprofile.sex = 'male'
        self.userprofile.addressment = 'own addressment'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("testovací šablona", interaction.summary)
        self.assertIn("own addressment", interaction.summary)
        self.assertIn("Vazeny pane", interaction.summary)

    def test_autocom_en(self):
        self.userprofile.sex = 'unknown'
        self.userprofile.language = 'en'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
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
