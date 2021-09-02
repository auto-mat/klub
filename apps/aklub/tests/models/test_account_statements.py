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
import json
from unittest.mock import patch

from django.core.files import File
from django.test import TestCase
from django.test.utils import override_settings

from model_mommy import mommy

from ..utils import RunCommitHooksMixin
from ... import darujme
from ...models import (
    AccountStatements,
    AdministrativeUnit,
    DonorPaymentChannel,
    Payment,
    ProfileEmail,
    Telephone,
    UserProfile,
)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class AccountStatementTests(RunCommitHooksMixin, TestCase):
    fixtures = ["conditions", "users"]

    def setUp(self):
        self.unit = AdministrativeUnit.objects.get(pk=1)

    def test_bank_new_statement_fio(self):
        recipient_account = mommy.make(
            "aklub.bankaccount",
            bank_account_number="2400063333/2010",
            administrative_unit=self.unit,
        )
        with open("apps/aklub/test_data/Pohyby_5_2016.csv", "rb") as f:
            a = AccountStatements(
                csv_file=File(f), type="account", administrative_unit=self.unit
            )
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
        self.assertEqual(a1.date_from, datetime.date(day=25, month=1, year=2016))
        self.assertEqual(a1.date_to, datetime.date(day=31, month=1, year=2016))

        p1 = Payment.objects.get(account=2150508001)
        self.assertEqual(p1.date, datetime.date(day=18, month=1, year=2016))
        self.assertEqual(p1.amount, 250)
        self.assertEqual(p1.account, "2150508001")
        self.assertEqual(p1.bank_code, "5500")
        self.assertEqual(p1.VS, "120127010")
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "12321")
        self.assertEqual(p1.KS, "0101")
        self.assertEqual(p1.user_identification, "Account note")
        self.assertEqual(p1.type, "bank-transfer")
        self.assertEqual(p1.done_by, "Done by")
        self.assertEqual(p1.account_name, "Testing user account")
        self.assertEqual(p1.bank_name, "Raiffeisenbank a.s.")
        self.assertEqual(p1.transfer_note, "Testing user note")
        self.assertEqual(p1.currency, "CZK")
        self.assertEqual(p1.recipient_message, "Message for recepient")
        self.assertEqual(p1.operation_id, "12366")
        self.assertEqual(p1.transfer_type, "Bezhotovostní příjem")
        self.assertEqual(p1.specification, "Account specification")
        self.assertEqual(p1.order_id, "1232")
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)
        self.assertEqual(p1.recipient_account, recipient_account)

        self.assertEqual(
            donor_channel.payment_set.get(date=datetime.date(2016, 1, 18)),
            a1.payment_set.get(account=2150508001),
        )

    def test_bank_new_statement_cs(self):
        recipient_account = mommy.make(
            "aklub.bankaccount",
            bank_account_number="99999999/2010",
            administrative_unit=self.unit,
        )
        with open("apps/aklub/test_data/Pohyby_cs.csv", "rb") as f:
            a = AccountStatements(
                csv_file=File(f), type="account_cs", administrative_unit=self.unit
            )
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 3)
        self.assertEqual(a1.date_from, datetime.date(day=10, month=2, year=2019))
        self.assertEqual(a1.date_to, datetime.date(day=11, month=3, year=2019))
        p1 = Payment.objects.get(account="20000-92392323")
        self.assertEqual(p1.date, datetime.date(day=11, month=3, year=2019))
        self.assertEqual(p1.amount, 1000)
        self.assertEqual(p1.account, "20000-92392323")
        self.assertEqual(p1.bank_code, "0800")
        self.assertEqual(p1.VS, "120127010")
        self.assertEqual(p1.VS2, "120127010")
        self.assertEqual(p1.SS, "5")
        self.assertEqual(p1.KS, "0")
        self.assertEqual(p1.user_identification, "")
        self.assertEqual(p1.type, "bank-transfer")
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Test Name")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "Message for sender 1")
        self.assertEqual(p1.currency, None)
        self.assertEqual(p1.recipient_message, "Message for recepien 1")
        self.assertEqual(p1.operation_id, "201903110000301585001001")
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)
        self.assertEqual(p1.recipient_account, recipient_account)

        self.assertEqual(
            donor_channel.payment_set.get(date=datetime.date(2019, 3, 11)),
            a1.payment_set.get(account="20000-92392323"),
        )

    def test_bank_new_statement_kb(self):
        recipient_account = mommy.make(
            "aklub.bankaccount",
            bank_account_number="999-99999999/2010",
            administrative_unit=self.unit,
        )
        with open("apps/aklub/test_data/pohyby_kb.csv", "rb") as f:
            a = AccountStatements(
                csv_file=File(f), type="account_kb", administrative_unit=self.unit
            )
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 3)
        self.assertEqual(a1.date_from, datetime.date(day=1, month=2, year=2010))
        self.assertEqual(a1.date_to, datetime.date(day=3, month=2, year=2010))

        p1 = Payment.objects.get(account="28937-32323234")
        self.assertEqual(p1.date, datetime.date(day=1, month=2, year=2010))
        self.assertEqual(p1.amount, 500)
        self.assertEqual(p1.account, "28937-32323234")
        self.assertEqual(p1.bank_code, "9999")
        self.assertEqual(p1.VS, "120127010")
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "3232")
        self.assertEqual(p1.KS, "23")
        self.assertEqual(p1.user_identification, "")
        self.assertEqual(p1.type, "bank-transfer")
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Protiucet_name")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "TEST1, ")
        self.assertEqual(p1.currency, None)
        self.assertEqual(p1.recipient_message, "Z    CK-73782378278")
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)
        self.assertEqual(p1.recipient_account, recipient_account)

        self.assertEqual(
            donor_channel.payment_set.get(date=datetime.date(2010, 2, 1)),
            a1.payment_set.get(account="28937-32323234"),
        )

    def test_bank_new_statement_csob(self):
        recipient_account = mommy.make(
            "aklub.bankaccount",
            bank_account_number="99999999/0300",
            administrative_unit=self.unit,
        )
        with open("apps/aklub/test_data/pohyby_csob.csv", "rb") as f:
            a = AccountStatements(
                csv_file=File(f), type="account_csob", administrative_unit=self.unit
            )
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
        self.assertEqual(a1.date_from, datetime.date(day=19, month=7, year=2019))
        self.assertEqual(a1.date_to, datetime.date(day=2, month=8, year=2019))

        p1 = Payment.objects.get(account="99999999")
        self.assertEqual(p1.date, datetime.date(day=19, month=7, year=2019))
        self.assertEqual(p1.amount, 200)
        self.assertEqual(p1.account, "99999999")
        self.assertEqual(p1.bank_code, "0600")
        self.assertEqual(p1.VS, "120127010")
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "9999")
        self.assertEqual(p1.KS, "1")
        self.assertEqual(p1.user_identification, "")
        self.assertEqual(p1.type, "bank-transfer")
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "TEST USER 1")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "")
        self.assertEqual(p1.currency, "CZK")
        self.assertEqual(p1.recipient_message, "We must test")
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)
        self.assertEqual(p1.recipient_account, recipient_account)

        self.assertEqual(
            donor_channel.payment_set.get(date=datetime.date(2019, 7, 19)),
            a1.payment_set.get(account="99999999"),
        )

    def test_bank_new_statement_sberbank(self):
        recipient_account = mommy.make(
            "aklub.bankaccount",
            bank_account_number="9999999999/0800",
            administrative_unit=self.unit,
        )
        with open("apps/aklub/test_data/pohyby_sberbank.txt", "rb") as f:
            a = AccountStatements(
                csv_file=File(f), type="account_sberbank", administrative_unit=self.unit
            )
            a.clean()
            a.save()

        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 4)
        self.assertEqual(a1.date_from, None)
        self.assertEqual(a1.date_to, None)

        p1 = Payment.objects.get(account="9999999999")
        self.assertEqual(p1.date, datetime.date(day=13, month=8, year=2019))
        self.assertEqual(p1.amount, 1000)
        self.assertEqual(p1.account, "9999999999")
        self.assertEqual(p1.bank_code, "9999")
        self.assertEqual(p1.VS, "120127010")
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "")
        self.assertEqual(p1.KS, "999")
        self.assertEqual(p1.user_identification, "")
        self.assertEqual(p1.type, "bank-transfer")
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Tester TEST")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, None)
        self.assertEqual(p1.currency, "CZK")
        self.assertEqual(p1.recipient_message, "MESSAGE TEST ONE")
        self.assertEqual(p1.operation_id, None)
        self.assertEqual(p1.transfer_type, "kreditní")
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)
        self.assertEqual(p1.recipient_account, recipient_account)

        self.assertEqual(
            donor_channel.payment_set.get(date=datetime.date(2019, 8, 13)),
            a1.payment_set.get(account="9999999999"),
        )

    def test_bank_new_statement_raiffeisenbank(self):
        recipient_account = mommy.make(
            "aklub.bankaccount",
            bank_account_number="233223/12",
            administrative_unit=self.unit,
        )
        with open("apps/aklub/test_data/pohyby_raiffeisenbank.csv", "rb") as f:
            a = AccountStatements(
                csv_file=File(f),
                type="account_raiffeisenbank",
                administrative_unit=self.unit,
            )
            a.clean()
            a.save()
        donor_channel = DonorPaymentChannel.objects.get(VS=120127010)

        self.run_commit_hooks()
        a1 = AccountStatements.objects.get(pk=a.pk)
        self.assertEqual(len(a1.payment_set.all()), 3)
        self.assertEqual(a1.date_from, None)
        self.assertEqual(a1.date_to, None)

        p1 = Payment.objects.get(account="23")
        self.assertEqual(p1.date, datetime.date(day=1, month=2, year=2018))
        self.assertEqual(p1.amount, 102)
        self.assertEqual(p1.account, "23")
        self.assertEqual(p1.bank_code, "23")
        self.assertEqual(p1.VS, "120127010")
        self.assertEqual(p1.VS2, None)
        self.assertEqual(p1.SS, "")
        self.assertEqual(p1.KS, "23322")
        self.assertEqual(p1.user_identification, "")
        self.assertEqual(p1.type, "bank-transfer")
        self.assertEqual(p1.done_by, "")
        self.assertEqual(p1.account_name, "Mr. Test")
        self.assertEqual(p1.bank_name, "")
        self.assertEqual(p1.transfer_note, "note")
        self.assertEqual(p1.currency, "CZK")
        self.assertEqual(p1.recipient_message, "message")
        self.assertEqual(p1.operation_id, "1")
        self.assertEqual(p1.transfer_type, None)
        self.assertEqual(p1.specification, None)
        self.assertEqual(p1.order_id, None)
        self.assertEqual(p1.user_donor_payment_channel, donor_channel)
        self.assertEqual(p1.recipient_account, recipient_account)

        self.assertEqual(
            donor_channel.payment_set.get(date=datetime.date(2018, 2, 1)),
            a1.payment_set.get(account="23"),
        )


@override_settings(CELERY_ALWAYS_EAGER=True)
class TestDarujmeCheck(TestCase):
    def setUp(self):

        self.unit1 = mommy.make("aklub.AdministrativeUnit", name="test_unit")
        self.unit2 = mommy.make("aklub.AdministrativeUnit", name="test_unit_2")
        self.event = mommy.make("events.Event", name="test_event")
        self.api_acc = mommy.make(
            "aklub.ApiAccount",
            project_name="test_project",
            project_id="22222",
            api_id="11111",
            api_secret="secret_hash",
            api_organization_id="123",
            event=self.event,
            administrative_unit=self.unit1,
        )

    @patch("aklub.darujme.requests.get")
    def run_check_darujme(self, mock_get):
        with open("apps/aklub/test_data/darujme_response.json") as json_file:
            mock_get.return_value.json.return_value = json.load(json_file)
            mock_get.return_value.status_code = 200
        darujme.check_for_new_payments()

    def test_check_new_payments(self):
        """
        testing new darujme project => create all data
        """
        self.run_check_darujme()
        # total of 3 users: 2 valid and 1 invalid (so not saved)
        self.assertTrue(UserProfile.objects.count(), 2)

        # user doesnt exist because he has no valid payment
        self.assertFalse(
            ProfileEmail.objects.filter(email="trickyone@test.cz").exists()
        )

        # user exists => has 2 valid payments and 1 invalid
        profile_email = ProfileEmail.objects.get(email="real@one.com")
        self.assertTrue(profile_email.is_primary)
        # check profile
        user = profile_email.user
        self.assertEqual(user.first_name, "Real")
        self.assertEqual(user.last_name, "One")
        self.assertEqual(user.street, "My Home")
        self.assertEqual(user.city, "In city")
        self.assertEqual(user.zip_code, "999")
        self.assertEqual(user.country, "Slovenská republika")
        self.assertListEqual(list(user.administrative_units.all()), [self.unit1])
        telephones = user.telephone_set.all()
        # check telephone
        self.assertEqual(telephones.count(), 1)
        telephone = telephones.first()
        self.assertEqual(telephone.telephone, "777888999")
        # check donor_payment_channel
        dpchs = user.userchannels.all()
        self.assertEqual(dpchs.count(), 1)
        dpch = dpchs.first()
        self.assertEqual(dpch.money_account, self.api_acc)
        self.assertEqual(dpch.regular_frequency, "monthly")
        self.assertEqual(dpch.regular_payments, "regular")
        self.assertEqual(dpch.regular_amount, 2000)
        self.assertEqual(
            dpch.expected_date_of_first_payment, datetime.date(2012, 11, 30)
        )
        self.assertEqual(dpch.end_of_regular_payments, datetime.date(2014, 11, 30))
        # check payments
        payments = dpch.payment_set.order_by("date")
        self.assertEqual(payments.count(), 2)

        self.assertEqual(payments[0].type, "darujme")
        self.assertEqual(payments[0].SS, "2")
        self.assertEqual(payments[0].date, datetime.date(2013, 12, 16))
        self.assertEqual(payments[0].operation_id, "12")
        self.assertEqual(payments[0].amount, 500)
        self.assertEqual(payments[0].account_name, "Real One")
        self.assertEqual(payments[0].user_identification, "Real@one.com")
        self.assertEqual(payments[0].recipient_account, self.api_acc)

        self.assertEqual(payments[1].type, "darujme")
        self.assertEqual(payments[1].SS, "2")
        self.assertEqual(payments[1].date, datetime.date(2014, 1, 16))
        self.assertEqual(payments[1].operation_id, "13")
        self.assertEqual(payments[1].amount, 500)
        self.assertEqual(payments[1].account_name, "Real One")
        self.assertEqual(payments[1].user_identification, "Real@one.com")
        self.assertEqual(payments[1].recipient_account, self.api_acc)

        # user exists => has 1 valid payments (second one is waiting for sent to organization)
        profile_email = ProfileEmail.objects.get(email="big@tester.com")
        self.assertTrue(profile_email.is_primary)
        # check profile
        user = profile_email.user
        self.assertEqual(user.first_name, "Testerek")
        self.assertEqual(user.last_name, "Teme")
        self.assertEqual(user.street, "i dont want to")
        self.assertEqual(user.city, "")
        self.assertEqual(user.zip_code, "")
        self.assertEqual(user.country, "Česká republika")
        self.assertListEqual(list(user.administrative_units.all()), [self.unit1])
        telephones = user.telephone_set.all()
        # check telephone
        self.assertEqual(telephones.count(), 1)
        telephone = telephones.first()
        self.assertEqual(telephone.telephone, "999888777")
        # check donor_payment_channel
        dpchs = user.userchannels.all()
        self.assertEqual(dpchs.count(), 1)
        dpch = dpchs.first()
        self.assertEqual(dpch.money_account, self.api_acc)
        self.assertEqual(dpch.regular_frequency, None)
        self.assertEqual(dpch.regular_payments, "onetime")
        self.assertEqual(dpch.regular_amount, 1900)
        self.assertEqual(
            dpch.expected_date_of_first_payment, datetime.date(2012, 11, 22)
        )
        self.assertEqual(dpch.end_of_regular_payments, None)
        # check payments
        payments = dpch.payment_set.order_by("date")
        self.assertEqual(payments.count(), 1)

        self.assertEqual(payments[0].type, "darujme")
        self.assertEqual(payments[0].SS, "3")
        self.assertEqual(payments[0].date, datetime.date(2014, 1, 16))
        self.assertEqual(payments[0].operation_id, "15")
        self.assertEqual(payments[0].amount, 500)
        self.assertEqual(payments[0].account_name, "Testerek Teme")
        self.assertEqual(payments[0].user_identification, "big@tester.com")
        self.assertEqual(payments[0].recipient_account, self.api_acc)

    def test_check_run_repeatly(self):
        """
        cron job run repeatly without changes in api => no duplicite data
        """
        self.run_check_darujme()
        self.run_check_darujme()
        self.run_check_darujme()

        self.assertEqual(ProfileEmail.objects.count(), 2)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(Telephone.objects.count(), 2)
        self.assertEqual(DonorPaymentChannel.objects.count(), 2)
        self.assertEqual(Payment.objects.count(), 3)

    def test_pair_with_existed_data(self):
        """
        user and dpch exists already
        => create new telephone
        => do not update userprofile (only add new administrative_unit)
        => update donor payment channel
        => pair payments
        """
        user = mommy.make(
            "aklub.UserProfile",
            first_name="Robert",
            last_name="Mad",
            street="a",
            city="b",
            zip_code="111",
            country="Česká republika",
            administrative_units=[self.unit2],
        )
        profile_email = mommy.make(
            "aklub.ProfileEmail", email="real@one.com", user=user
        )
        mommy.make("aklub.Telephone", user=user, telephone="555666777")
        bank_acc = mommy.make("aklub.BankAccount", administrative_unit=self.unit1)
        mommy.make(
            "aklub.DonorPaymentChannel",
            event=self.event,
            money_account=bank_acc,  # has diff bank_acc of same unit
            regular_amount=6600,
        )

        self.run_check_darujme()

        profile_email.refresh_from_db()
        self.assertFalse(profile_email.is_primary)
        # check profile (not updated)
        user = profile_email.user
        self.assertEqual(user.first_name, "Robert")
        self.assertEqual(user.last_name, "Mad")
        self.assertEqual(user.street, "a")
        self.assertEqual(user.city, "b")
        self.assertEqual(user.zip_code, "111")
        self.assertEqual(user.country, "Česká republika")
        self.assertListEqual(
            sorted(user.administrative_units.all().values_list("id", flat=True)),
            sorted([self.unit1.id, self.unit2.id]),
        )
        telephones = user.telephone_set.all()
        # check new telephone
        self.assertEqual(telephones.count(), 2)
        telephone = telephones.last()
        self.assertEqual(telephone.telephone, "777888999")

        # check donor_payment_channel (updated)
        dpchs = user.userchannels.all()
        self.assertEqual(dpchs.count(), 1)
        dpch = dpchs.first()
        self.assertEqual(dpch.money_account, self.api_acc)
        self.assertEqual(dpch.regular_frequency, "monthly")
        self.assertEqual(dpch.regular_payments, "regular")
        self.assertEqual(dpch.regular_amount, 2000)
        self.assertEqual(
            dpch.expected_date_of_first_payment, datetime.date(2012, 11, 30)
        )
        self.assertEqual(dpch.end_of_regular_payments, datetime.date(2014, 11, 30))
        # check payments
        payments = dpch.payment_set.order_by("date")
        self.assertEqual(payments.count(), 2)


@override_settings(
    CELERY_ALWAYS_EAGER=True,
)
class TestPairPayments(TestCase):
    """Test AccountStatement. payment_pair()"""

    def setUp(self):
        self.payment_vs = mommy.make(
            "aklub.Payment", id=1, VS=123, account=999999, bank_code=1111
        )
        self.payment_no_vs = mommy.make(
            "aklub.Payment", id=2, account=999999, bank_code=1111
        )

        self.administrative_unit_1 = mommy.make(
            "aklub.AdministrativeUnit", name="test1"
        )
        self.administrative_unit_2 = mommy.make(
            "aklub.AdministrativeUnit", name="test2"
        )

        self.user_bank_acc = mommy.make(
            "aklub.UserBankAccount", bank_account_number="999999/1111"
        )

        self.bank_account_1 = mommy.make(
            "aklub.BankAccount", id=1, administrative_unit=self.administrative_unit_1
        )
        self.bank_account_2 = mommy.make(
            "aklub.BankAccount", id=2, administrative_unit=self.administrative_unit_2
        )

        self.donor_payment_channel_1 = mommy.make(
            "aklub.DonorPaymentChannel",
            VS=123,
            user_bank_account=self.user_bank_acc,
            money_account=self.bank_account_1,
        )
        self.donor_payment_channel_1_1 = mommy.make(
            "aklub.DonorPaymentChannel",
            VS=1234,
            user_bank_account=self.user_bank_acc,
            money_account=self.bank_account_1,
        )
        self.donor_payment_channel_2 = mommy.make(
            "aklub.DonorPaymentChannel",
            VS=123,
            user_bank_account=self.user_bank_acc,
            money_account=self.bank_account_2,
        )

    def test_pairing_vs(self):
        """
        Test if Variable symbol exist and there is more than one user_bank_acc with same number=
        pair with DPCH with same administrative unit and VS
        """
        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_1,
            payment_set=[self.payment_vs],
        )

        return_value = account_statement.payment_pair(self.payment_vs)
        payment = Payment.objects.get(id=1)

        self.assertEqual(
            payment.user_donor_payment_channel, self.donor_payment_channel_1
        )
        self.assertEqual(return_value, True)

        self.assertTrue(account_statement.pair_log == "")

    def test_pairing_user_bank_acc(self):
        """Prefer pair with DPCH with unique user bank account in administrative unit"""
        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_2,
            payment_set=[self.payment_vs],
        )

        return_value = account_statement.payment_pair(self.payment_vs)
        payment = Payment.objects.get(id=1)

        self.assertEqual(
            payment.user_donor_payment_channel, self.donor_payment_channel_2
        )
        self.assertEqual(return_value, True)

        self.assertTrue(account_statement.pair_log == "")

    def test_pairing_multiple_user_bank_acc_false(self):
        """Test if Variable symbol not exist and multiple user_bank_acc exist in one administrative unit"""

        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_1,
            payment_set=[self.payment_no_vs],
        )

        return_value = account_statement.payment_pair(self.payment_no_vs)
        payment = Payment.objects.get(id=2)

        self.assertEqual(payment.user_donor_payment_channel, None)
        self.assertEqual(return_value, False)
        self.assertTrue(
            "Vícero platebních kanálu s tímto uživatelským bankovním účtem //Platební kanál s tímto VS neexistuje\n"
            in account_statement.pair_log,
        )

    def test_pairing_no_dpch_false(self):
        """Test if donor_payment_channel is not found"""
        payment = mommy.make("aklub.Payment", VS=12345, id=3)
        account_statement = mommy.make(
            "aklub.AccountStatements",
            administrative_unit=self.administrative_unit_1,
            payment_set=[payment],
        )

        return_value = account_statement.payment_pair(payment)
        payment = Payment.objects.get(id=3)

        self.assertEqual(payment.user_donor_payment_channel, None)
        self.assertEqual(return_value, False)
        self.assertTrue(
            "Platební kanál s tímto uživatelským bankovním účtem neexistuje //Platební kanál s tímto VS neexistuje\n"
            in account_statement.pair_log,
        )
