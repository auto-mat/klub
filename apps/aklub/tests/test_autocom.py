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

from interactions.models import Interaction

from model_mommy import mommy


from .. import autocom


class AutocomTest(TestCase):
    def setUp(self):
        self.userprofile = mommy.make("aklub.userprofile", sex='male', street='test_street', city='test_city', zip_code='111222', id=111)
        self.email = mommy.make('aklub.profileemail', is_primary=True, email='autotest@email.com', user=self.userprofile)
        self.telephone = mommy.make('aklub.telephone', is_primary=True, telephone=111222333, user=self.userprofile)
        self.event = mommy.make('aklub.event', created=datetime.date(2010, 10, 10))
        self.au = mommy.make('aklub.administrativeunit', name='test', slug='test')
        self.bankaccount = mommy.make('aklub.bankaccount', bank_account_number=11111, administrative_unit=self.au)
        self.payment_channel = mommy.make(
                                    'aklub.donorpaymentchannel',
                                    user=self.userprofile,
                                    event=self.event,
                                    money_account=self.bankaccount,
                                    VS='123123123',
                                    regular_frequency='monthly',
                                    regular_amount=1000,
                                )
        self.payment = mommy.make('aklub.payment', amount=500, user_donor_payment_channel=self.payment_channel, date="2016-01-02")
        nc = mommy.make('flexible_filter_conditions.namedcondition')
        c = mommy.make('flexible_filter_conditions.condition', operation="or", negate=True, named_condition=nc)
        mommy.make(
            'flexible_filter_conditions.terminalcondition',
            variable="action",
            value="test-autocomm",
            operation="==",
            condition=c,
        )
        inter_category = mommy.make('interactions.interactioncategory', category='testcategory')
        inter_type = mommy.make('interactions.interactiontype', category=inter_category, name='testtype', send_email=True)
        unit = mommy.make('aklub.administrativeunit', name='testAU')
        from ..models import AutomaticCommunication
        AutomaticCommunication.objects.create(
            method_type=inter_type,
            condition=nc,
            template="""
                        testovací šablona
                        Vazen{y|a} {pane|pani}
                        $addressment
                        $last_name_vokativ
                        $name
                        $firstname
                        $surname
                        $street
                        $city
                        $zipcode
                        $email
                        $telephone
                        $regular_amount
                        $regular_frequency
                        $var_symbol
                        $last_payment_amount
                        $auth_token
                     """,
            template_en="""
                        test template
                        Dear {sir|miss}
                        $addressment
                        $last_name_vokativ
                        $name
                        $firstname
                        $surname
                        $street
                        $city
                        $zipcode
                        $email
                        $telephone
                        $regular_amount
                        $regular_frequency
                        $var_symbol
                        $last_payment_amount
                        $auth_token
                        """,
            subject="Testovací komunikace",
            subject_en="Testing interaction",
            administrative_unit=unit,
          )

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

    def test_autocom_no_addressment_en(self):
        self.userprofile.sex = 'male'
        self.userprofile.language = 'en'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        self.assertIn("test template", interaction.summary)
        self.assertIn("Auto*Mat friend", interaction.summary)
        self.assertIn("Dear sir", interaction.summary)

    def test_autocom(self):
        self.userprofile.last_name = 'last_user'
        self.userprofile.first_name = 'first_user'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        # name
        self.assertTrue("testovací šablona" in interaction.summary)
        self.assertTrue("Vazeny pane" in interaction.summary)
        self.assertTrue("First_Usere" in interaction.summary)
        self.assertTrue("Last_Usere" in interaction.summary)
        self.assertTrue("first_user" in interaction.summary)
        self.assertTrue("last_user" in interaction.summary)
        # address
        self.assertTrue("test_street" in interaction.summary)
        self.assertTrue("test_city" in interaction.summary)
        self.assertTrue("111222" in interaction.summary)
        # contact
        self.assertTrue("autotest@email.com" in interaction.summary)
        self.assertTrue("111222333" in interaction.summary)
        # dpch
        self.assertTrue("123123123" in interaction.summary)
        self.assertTrue("měsíčně" in interaction.summary)
        self.assertTrue("1000" in interaction.summary)
        # token
        url = "example.com/cs/email_confirmation/test_unit/?url_auth_token=AAAAb1wKAecO8DcJ3HQqlu5XWGE%3AlvBqArDpLyHz-s5MiGfBf4_Kfsg"
        self.assertTrue(url in interaction.summary)

    def test_autocom_en(self):
        self.userprofile.sex = 'unknown'
        self.userprofile.language = 'en'
        self.userprofile.last_name = 'last_user'
        self.userprofile.first_name = 'first_user'
        self.userprofile.save()
        autocom.check(event=self.event, action="test-autocomm")
        interaction = Interaction.objects.get(user=self.userprofile)
        # name
        self.assertTrue("test template" in interaction.summary)
        self.assertTrue("Dear sir/miss" in interaction.summary)
        self.assertTrue("first_user" in interaction.summary)
        self.assertTrue("last_user" in interaction.summary)
        self.assertTrue("first_user" in interaction.summary)
        self.assertTrue("last_user" in interaction.summary)
        # address
        self.assertTrue("test_street" in interaction.summary)
        self.assertTrue("test_city" in interaction.summary)
        self.assertTrue("111222" in interaction.summary)
        # contact
        self.assertTrue("autotest@email.com" in interaction.summary)
        self.assertTrue("111222333" in interaction.summary)
        # dpch
        self.assertTrue("123123123" in interaction.summary)
        self.assertTrue("monthly" in interaction.summary)
        self.assertTrue("1000" in interaction.summary)
        # token
        url = "example.com/cs/email_confirmation/test_unit/?url_auth_token=AAAAb1wKAecO8DcJ3HQqlu5XWGE%3AlvBqArDpLyHz-s5MiGfBf4_Kfsg"
        self.assertTrue(url in interaction.summary)


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
