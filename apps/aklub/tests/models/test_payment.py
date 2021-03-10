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
from aklub.admin import add_user_bank_acc_to_dpch
from aklub.models import DonorPaymentChannel

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase
from django.test.client import RequestFactory

from model_mommy import mommy


class TestPersonName(TestCase):
    """ Test Result.person_name """

    def test_result_str(self):
        au = mommy.make(
            'aklub.AdministrativeUnit'
        )
        user_profile = mommy.make(
            "aklub.UserProfile",
            first_name="Foo",
            last_name="Name",
        )
        mommy.make(
            'events.event',
            id=22,
            administrative_units=[au, ],
        )
        result = mommy.make(
            "aklub.Payment",
            campaign__name="Foo campaign",
            user_donor_payment_channel__user=user_profile,
            user_donor_payment_channel__bank_account__id=1,
            user_donor_payment_channel__event__id=22,
        )
        self.assertEqual(result.person_name(), 'Name Foo')

    def test_no_user(self):
        """ Test with no user set """
        result = mommy.make(
            "aklub.Payment",
            campaign__name="Foo campaign",
        )
        self.assertEqual(result.person_name(), None)


class TestUserBankAccountRewrite(TestCase):
    def setUp(self):
        au = mommy.make(
            "aklub.AdministrativeUnit",
            name="test",
        )
        self.user_profile = mommy.make(
            "aklub.UserProfile",
            first_name="Foo",
            last_name="Name",
            administrative_units=(au,),
        )

        money_acc = mommy.make(
            "aklub.MoneyAccount",
            administrative_unit=au,
        )
        user_bank_acc = mommy.make(
            "aklub.UserBankAccount",
            bank_account_number="2332222/2222",
        )
        event = mommy.make(
            'events.event',
            administrative_units=[au, ],
        )
        self.donor_payment_channel = mommy.make(
            "aklub.DonorPaymentChannel",
            user=self.user_profile,
            user_bank_account=user_bank_acc,
            money_account=money_acc,
            event=event,
        )

        self.request = RequestFactory().post("/aklub/payments")
        self.request.session = 'session'
        self.request._messages = FallbackStorage(self.request)

    def test_dpch_user_bank_acc_rewrite(self):
        """
        test if user_bank_account_number is changed by action add_user_bank_acc_to_dpch
        """
        payment = mommy.make(
            "aklub.Payment",
            amount="111",
            date="2010-11-11",
            account="111111",
            bank_code="1111",
            user_donor_payment_channel=self.donor_payment_channel,
        )
        add_user_bank_acc_to_dpch(None, self.request, [payment, ])

        dpch = DonorPaymentChannel.objects.get(user=self.user_profile)
        self.assertEqual(dpch.user_bank_account.bank_account_number, "111111/1111")

    def test_dpch_user_bank_acc_not_rewrite(self):
        """
        test that user_bank_account_do not rewrite because there is bank_code missing
        """
        payment = mommy.make(
            "aklub.Payment",
            amount="111",
            date="2010-11-11",
            account="111111",
            user_donor_payment_channel=self.donor_payment_channel,
        )
        add_user_bank_acc_to_dpch(None, self.request, [payment, ])

        dpch = DonorPaymentChannel.objects.get(user=self.user_profile)
        self.assertEqual(dpch.user_bank_account.bank_account_number, "2332222/2222")

    def test_no_dpch_user_bank_acc_not_rewrite(self):
        """
        test that user_bank_account_do not rewrite because there is not donor_payment_channel
        """
        payment = mommy.make(
            "aklub.Payment",
            amount="111",
            date="2010-11-11",
            account="111111",
            bank_code="1111",
        )
        add_user_bank_acc_to_dpch(None, self.request, [payment, ])

        dpch = DonorPaymentChannel.objects.get(user=self.user_profile)
        self.assertEqual(dpch.user_bank_account.bank_account_number, "2332222/2222")
